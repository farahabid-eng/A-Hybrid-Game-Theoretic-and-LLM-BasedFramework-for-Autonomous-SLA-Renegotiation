from datetime import datetime

from sla_renegotiation.clauses.generator import generate_rc
from sla_renegotiation.domain.enums import NegotiationRole, RenegotiationStatus
from sla_renegotiation.domain.models import (
    SLOConfig,
    StakeholderProfile,
    Violation,
    Workflow,
)
from sla_renegotiation.negotiation.agents import client_agent, provider_agent
from sla_renegotiation.negotiation.agreement import check_agreement
from sla_renegotiation.negotiation.graph import _format_history
from sla_renegotiation.profiles.builder import build_profile
from sla_renegotiation.storage.in_memory import WorkflowStore
from sla_renegotiation.storage.sla_seeds import get_sla
from sla_renegotiation.zopa.calculator import compute_multi_metric_zopa, narrow_zopa


class WorkflowService:
    def __init__(self, store: WorkflowStore) -> None:
        self._store = store

    def create_workflow(self, sla_id: str, max_rounds: int = 10) -> Workflow:
        sla = get_sla(sla_id)
        if not sla:
            raise ValueError(f"SLA template '{sla_id}' not found")

        workflow = Workflow(
            sla_id=sla_id,
            max_rounds=max_rounds,
            status=RenegotiationStatus.PENDING,
        )

        # Copy SLA-level SLO configs (with BATNAs) to the workflow
        sla_configs = self._store.get_sla_slo_configs(sla_id)
        if sla_configs:
            workflow_configs = [
                SLOConfig(
                    metric=c.metric,
                    unit=c.unit,
                    agreed_value=c.agreed_value,
                    description=c.description,
                    event_type=c.event_type,
                    time_to_repair=c.time_to_repair,
                    client_batna=c.client_batna,
                    provider_batna=c.provider_batna,
                )
                for c in sla_configs
            ]
        else:
            workflow_configs = [
                SLOConfig(
                    metric=slo.metric,
                    unit=slo.unit,
                    agreed_value=slo.target_value,
                    description=slo.description,
                    event_type=slo.event_type,
                    time_to_repair=slo.time_to_repair,
                )
                for slo in sla.slos
            ]

        # Copy SLA-level profiles to the workflow
        client_profile = self._store.get_sla_profile(sla_id, "client")
        provider_profile = self._store.get_sla_profile(sla_id, "provider")
        if client_profile:
            workflow.client_profile = client_profile
        if provider_profile:
            workflow.provider_profile = provider_profile

        self._store.save(workflow)
        self._store.save_slo_configs(workflow.id, workflow_configs)
        return workflow

    def set_batnas(
        self,
        workflow_id: str,
        client_batnas: dict[str, float],
        provider_batnas: dict[str, float],
    ) -> Workflow:
        workflow = self._store.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        slo_configs = self._store.get_slo_configs(workflow_id)
        slo_metrics = {c.metric for c in slo_configs}

        for m in client_batnas:
            if m not in slo_metrics:
                raise ValueError(f"Unknown metric: {m}")
        for m in provider_batnas:
            if m not in slo_metrics:
                raise ValueError(f"Unknown metric: {m}")

        self._store.update_slo_batnas(workflow_id, client_batnas, provider_batnas)
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        result = self._store.get(workflow_id)
        assert result is not None
        return result

    def set_profile(
        self,
        workflow_id: str,
        role: NegotiationRole,
        objectives: list[str],
        priorities: dict[str, float],
        flexibility_margins: dict[str, float],
        context_description: str,
        tone: str = "neutral",
    ) -> Workflow:
        workflow = self._store.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        profile = StakeholderProfile(
            role=role,
            objectives=objectives,
            priorities=priorities,
            flexibility_margins=flexibility_margins,
            context_description=context_description,
            tone=tone,
        )

        if role == NegotiationRole.CLIENT:
            workflow.client_profile = profile
        else:
            workflow.provider_profile = profile

        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        assert workflow is not None
        return workflow

    def generate_profile(
        self, workflow_id: str, role: NegotiationRole, context: str
    ) -> StakeholderProfile:
        slo_configs = self._store.get_slo_configs(workflow_id)
        workflow = self._store.get(workflow_id)
        sla = get_sla(workflow.sla_id) if workflow and workflow.sla_id else None
        return build_profile(context, role, sla=sla, slo_configs=slo_configs)

    def simulate_violation(
        self,
        workflow_id: str,
        event_type: str,
        observed_value: float,
    ) -> Workflow:
        from sla_renegotiation.domain.enums import EventType

        workflow = self._store.get(workflow_id)
        if not workflow:
            raise ValueError("Workflow not found")

        evt = EventType(event_type)
        metric = evt.value.removesuffix("_violation")

        slo_configs = self._store.get_slo_configs(workflow_id)
        matching = [s for s in slo_configs if s.metric == metric]
        if not matching:
            raise ValueError(f"No SLO for metric '{metric}'")

        slo = matching[0]
        violation = Violation(
            event_type=evt,
            observed_value=observed_value,
            agreed_value=slo.agreed_value,
            unit=slo.unit,
        )
        workflow.violation = violation
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def run_profiling(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow or not workflow.client_profile or not workflow.provider_profile:
            return None
        if not workflow.violation:
            return None

        workflow.status = RenegotiationStatus.ZOPA_CALCULATION
        self._store.save(workflow)

        slo_configs = self._store.get_slo_configs(workflow_id)

        workflow.zopa = compute_multi_metric_zopa(
            slo_configs,
            violated_metric=workflow.violation.metric,
        )

        if not workflow.zopa.feasible_range_per_metric:
            workflow.status = RenegotiationStatus.FAILED
        else:
            workflow.status = RenegotiationStatus.NEGOTIATING
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    async def run_negotiation_round(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if (
            not workflow
            or not workflow.client_profile
            or not workflow.provider_profile
            or not workflow.zopa
        ):
            return None

        if workflow.current_round >= workflow.max_rounds:
            workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
            self._store.save(workflow)
            return workflow

        history = _format_history(workflow.proposals)

        violated_metric = workflow.violation.metric if workflow.violation else "unknown"
        round_zopa = workflow.zopa

        client_proposal = None
        async for _, proposal in client_agent.stream_content(
            profile=workflow.client_profile,
            zopa=round_zopa,
            history=history,
            current_round=workflow.current_round + 1,
            max_rounds=workflow.max_rounds,
            violated_metric=violated_metric,
        ):
            if proposal:
                client_proposal = proposal
        if client_proposal:
            workflow.proposals.append(client_proposal)
        workflow.current_round += 1

        provider_proposal = None
        async for _, proposal in provider_agent.stream_content(
            profile=workflow.provider_profile,
            zopa=round_zopa,
            history=_format_history(workflow.proposals),
            current_round=workflow.current_round,
            max_rounds=workflow.max_rounds,
            violated_metric=violated_metric,
        ):
            if proposal:
                provider_proposal = proposal
        if provider_proposal:
            workflow.proposals.append(provider_proposal)

        # Narrow ZOPA after both proposals in the round
        if round_zopa:
            narrowed = round_zopa
            if client_proposal:
                narrowed = narrow_zopa(narrowed, client_proposal)
            if provider_proposal:
                narrowed = narrow_zopa(narrowed, provider_proposal)
            workflow.zopa = narrowed

        if (
            client_proposal
            and provider_proposal
            and check_agreement(client_proposal, provider_proposal)
        ):
            workflow.status = RenegotiationStatus.AGREED
        elif workflow.current_round >= workflow.max_rounds:
            workflow.status = RenegotiationStatus.MAX_ROUNDS_REACHED
        else:
            workflow.status = RenegotiationStatus.NEGOTIATING

        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def finalize(self, workflow_id: str) -> Workflow | None:
        workflow = self._store.get(workflow_id)
        if not workflow:
            return None
        workflow.rc = generate_rc(workflow)
        workflow.status = RenegotiationStatus.AGREED
        workflow.updated_at = datetime.now().isoformat()
        self._store.save(workflow)
        return workflow

    def get_workflow(self, workflow_id: str) -> Workflow | None:
        return self._store.get(workflow_id)

    def get_slo_configs(self, workflow_id: str) -> list[SLOConfig]:
        return self._store.get_slo_configs(workflow_id)

    # --- SLA-level methods ---

    def get_sla_slo_configs(self, sla_id: str) -> list[SLOConfig]:
        return self._store.get_sla_slo_configs(sla_id)

    def set_sla_batnas(
        self,
        sla_id: str,
        client_batnas: dict[str, float],
        provider_batnas: dict[str, float],
    ) -> None:
        configs = self._store.get_sla_slo_configs(sla_id)
        if not configs:
            sla = get_sla(sla_id)
            if not sla:
                raise ValueError(f"SLA template '{sla_id}' not found")
            configs = [
                SLOConfig(
                    metric=slo.metric,
                    unit=slo.unit,
                    agreed_value=slo.target_value,
                    description=slo.description,
                    event_type=slo.event_type,
                    time_to_repair=slo.time_to_repair,
                )
                for slo in sla.slos
            ]
            self._store.save_sla_slo_configs(sla_id, configs)

        slo_metrics = {c.metric for c in configs}
        for m in client_batnas:
            if m not in slo_metrics:
                raise ValueError(f"Unknown metric: {m}")
        for m in provider_batnas:
            if m not in slo_metrics:
                raise ValueError(f"Unknown metric: {m}")

        self._store.update_sla_batnas(sla_id, client_batnas, provider_batnas)

    def set_sla_profile(
        self,
        sla_id: str,
        role: NegotiationRole,
        objectives: list[str],
        priorities: dict[str, float],
        flexibility_margins: dict[str, float],
        context_description: str,
        tone: str = "neutral",
    ) -> None:
        profile = StakeholderProfile(
            role=role,
            objectives=objectives,
            priorities=priorities,
            flexibility_margins=flexibility_margins,
            context_description=context_description,
            tone=tone,
        )
        self._store.save_sla_profile(sla_id, role.value, profile)

    def get_sla_profile(self, sla_id: str, role: NegotiationRole) -> StakeholderProfile | None:
        return self._store.get_sla_profile(sla_id, role.value)

    def generate_sla_profile(
        self, sla_id: str, role: NegotiationRole, context: str
    ) -> StakeholderProfile:
        slo_configs = self._store.get_sla_slo_configs(sla_id)
        sla = get_sla(sla_id)
        return build_profile(context, role, sla=sla, slo_configs=slo_configs)
