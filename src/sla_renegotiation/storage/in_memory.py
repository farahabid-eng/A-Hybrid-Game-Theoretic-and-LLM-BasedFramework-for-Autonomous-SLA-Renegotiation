import asyncio
import json
import os
import sqlite3
from uuid import uuid4

from sla_renegotiation.config import settings
from sla_renegotiation.domain.enums import RenegotiationStatus
from sla_renegotiation.domain.models import (
    ZOPA,
    Proposal,
    RenegotiationClause,
    SLOConfig,
    StakeholderProfile,
    Violation,
    Workflow,
)


class WorkflowStore:
    def __init__(self, db_path: str | None = None) -> None:
        self._db_path = db_path or settings.db_path
        os.makedirs(os.path.dirname(self._db_path), exist_ok=True)
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._locks: dict[str, asyncio.Lock] = {}
        self._init_tables()

    def _init_tables(self) -> None:
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS workflows (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                sla_id TEXT,
                max_rounds INTEGER NOT NULL DEFAULT 10,
                current_round INTEGER NOT NULL DEFAULT 0,
                client_profile TEXT,
                provider_profile TEXT,
                violation TEXT,
                zopa TEXT,
                rc TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS slo_configs (
                workflow_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                unit TEXT NOT NULL,
                agreed_value REAL NOT NULL,
                description TEXT NOT NULL,
                event_type TEXT NOT NULL,
                time_to_repair INTEGER NOT NULL,
                PRIMARY KEY (workflow_id, metric)
            );

            CREATE TABLE IF NOT EXISTS sla_slo_configs (
                sla_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                unit TEXT NOT NULL,
                agreed_value REAL NOT NULL,
                description TEXT NOT NULL,
                event_type TEXT NOT NULL,
                time_to_repair INTEGER NOT NULL,
                PRIMARY KEY (sla_id, metric)
            );

            CREATE TABLE IF NOT EXISTS sla_profiles (
                sla_id TEXT NOT NULL,
                role TEXT NOT NULL,
                profile TEXT NOT NULL,
                PRIMARY KEY (sla_id, role)
            );

            CREATE TABLE IF NOT EXISTS proposals (
                id TEXT PRIMARY KEY,
                workflow_id TEXT NOT NULL,
                round_number INTEGER NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                structured_adjustments TEXT,
                timestamp TEXT NOT NULL
            );
        """)
        self._conn.commit()

    def save(self, workflow: Workflow) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO workflows
               (id, status, sla_id, max_rounds, current_round,
                client_profile, provider_profile, violation, zopa, rc,
                created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                workflow.id,
                workflow.status.value,
                workflow.sla_id or "",
                workflow.max_rounds,
                workflow.current_round,
                json.dumps(workflow.client_profile.model_dump())
                if workflow.client_profile
                else None,
                json.dumps(workflow.provider_profile.model_dump())
                if workflow.provider_profile
                else None,
                json.dumps(workflow.violation.model_dump()) if workflow.violation else None,
                json.dumps(workflow.zopa.model_dump()) if workflow.zopa else None,
                json.dumps(workflow.rc.model_dump()) if workflow.rc else None,
                workflow.created_at,
                workflow.updated_at,
            ),
        )
        self._conn.execute("DELETE FROM proposals WHERE workflow_id = ?", (workflow.id,))
        for p in workflow.proposals:
            self._conn.execute(
                """INSERT INTO proposals
                   (id, workflow_id, round_number, role, content, structured_adjustments, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    uuid4().hex[:12],
                    workflow.id,
                    p.round_number,
                    p.role.value if hasattr(p.role, "value") else p.role,
                    p.content,
                    json.dumps(p.structured_adjustments) if p.structured_adjustments else None,
                    p.timestamp,
                ),
            )
        self._conn.commit()

    def get(self, workflow_id: str) -> Workflow | None:
        row = self._conn.execute("SELECT * FROM workflows WHERE id = ?", (workflow_id,)).fetchone()
        if not row:
            return None
        return self._row_to_workflow(row)

    def list_all(self) -> list[Workflow]:
        rows = self._conn.execute("SELECT * FROM workflows").fetchall()
        return [self._row_to_workflow(r) for r in rows]

    def delete(self, workflow_id: str) -> None:
        self._conn.execute("DELETE FROM proposals WHERE workflow_id = ?", (workflow_id,))
        self._conn.execute("DELETE FROM slo_configs WHERE workflow_id = ?", (workflow_id,))
        self._conn.execute("DELETE FROM workflows WHERE id = ?", (workflow_id,))
        self._conn.commit()

    def delete_sla_data(self, sla_id: str) -> None:
        self._conn.execute("DELETE FROM sla_slo_configs WHERE sla_id = ?", (sla_id,))
        self._conn.execute("DELETE FROM sla_profiles WHERE sla_id = ?", (sla_id,))
        self._conn.commit()

    def _row_to_workflow(self, row: sqlite3.Row) -> Workflow:
        w = Workflow(
            id=row["id"],
            status=RenegotiationStatus(row["status"]),
            sla_id=row["sla_id"] or None,
            max_rounds=row["max_rounds"],
            current_round=row["current_round"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
        )
        if row["client_profile"]:
            w.client_profile = StakeholderProfile(**json.loads(row["client_profile"]))
        if row["provider_profile"]:
            w.provider_profile = StakeholderProfile(**json.loads(row["provider_profile"]))
        if row["violation"]:
            w.violation = Violation(**json.loads(row["violation"]))
        if row["zopa"]:
            w.zopa = ZOPA(**json.loads(row["zopa"]))
        if row["rc"]:
            w.rc = RenegotiationClause(**json.loads(row["rc"]))

        proposal_rows = self._conn.execute(
            "SELECT * FROM proposals WHERE workflow_id = ? ORDER BY round_number, timestamp",
            (row["id"],),
        ).fetchall()
        w.proposals = [self._row_to_proposal(r) for r in proposal_rows]
        return w

    @staticmethod
    def _row_to_proposal(row: sqlite3.Row) -> Proposal:
        return Proposal(
            round_number=row["round_number"],
            role=row["role"],
            content=row["content"],
            structured_adjustments=json.loads(row["structured_adjustments"])
            if row["structured_adjustments"]
            else None,
            timestamp=row["timestamp"],
        )

    def save_slo_configs(self, workflow_id: str, configs: list[SLOConfig]) -> None:
        for c in configs:
            self._conn.execute(
                """INSERT OR REPLACE INTO slo_configs
                   (workflow_id, metric, unit, agreed_value, description,
                    event_type, time_to_repair)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    workflow_id,
                    c.metric,
                    c.unit,
                    c.agreed_value,
                    c.description,
                    c.event_type.value if hasattr(c.event_type, "value") else c.event_type,
                    c.time_to_repair,
                ),
            )
        self._conn.commit()

    async def get_lock(self, workflow_id: str) -> asyncio.Lock:
        if workflow_id not in self._locks:
            self._locks[workflow_id] = asyncio.Lock()
        return self._locks[workflow_id]

    def get_slo_configs(self, workflow_id: str) -> list[SLOConfig]:
        rows = self._conn.execute(
            "SELECT * FROM slo_configs WHERE workflow_id = ?", (workflow_id,)
        ).fetchall()
        return [self._row_to_slo_config(r) for r in rows]

    @staticmethod
    def _row_to_slo_config(row: sqlite3.Row) -> SLOConfig:
        from sla_renegotiation.domain.enums import EventType

        return SLOConfig(
            metric=row["metric"],
            unit=row["unit"],
            agreed_value=row["agreed_value"],
            description=row["description"],
            event_type=EventType(row["event_type"]),
            time_to_repair=row["time_to_repair"],
        )

    # --- SLA-level helpers ---

    def save_sla_slo_configs(self, sla_id: str, configs: list[SLOConfig]) -> None:
        for c in configs:
            self._conn.execute(
                """INSERT OR REPLACE INTO sla_slo_configs
                   (sla_id, metric, unit, agreed_value, description,
                    event_type, time_to_repair)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    sla_id,
                    c.metric,
                    c.unit,
                    c.agreed_value,
                    c.description,
                    c.event_type.value if hasattr(c.event_type, "value") else c.event_type,
                    c.time_to_repair,
                ),
            )
        self._conn.commit()

    def get_sla_slo_configs(self, sla_id: str) -> list[SLOConfig]:
        rows = self._conn.execute(
            "SELECT * FROM sla_slo_configs WHERE sla_id = ?", (sla_id,)
        ).fetchall()
        return [self._row_to_slo_config(r) for r in rows]

    def save_sla_profile(self, sla_id: str, role: str, profile: StakeholderProfile) -> None:
        self._conn.execute(
            """INSERT OR REPLACE INTO sla_profiles (sla_id, role, profile)
               VALUES (?, ?, ?)""",
            (sla_id, role, json.dumps(profile.model_dump())),
        )
        self._conn.commit()

    def get_sla_profile(self, sla_id: str, role: str) -> StakeholderProfile | None:
        row = self._conn.execute(
            "SELECT profile FROM sla_profiles WHERE sla_id = ? AND role = ?",
            (sla_id, role),
        ).fetchone()
        if not row:
            return None
        return StakeholderProfile(**json.loads(row["profile"]))
