from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field

from sla_renegotiation.domain.enums import (
    EventType,
    NegotiationRole,
    RenegotiationStatus,
)


class SLODefinition(BaseModel):
    metric: str
    target_value: float
    unit: str
    description: str
    event_type: EventType
    time_to_repair: int


class SLOConfig(BaseModel):
    metric: str
    unit: str
    agreed_value: float
    description: str
    event_type: EventType
    time_to_repair: int


class SLATemplate(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    name: str
    description: str
    slos: list[SLODefinition]


class Violation(BaseModel):
    event_type: EventType
    observed_value: float
    agreed_value: float
    unit: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    time_to_repair: int | None = None
    description: str = ""

    @property
    def metric(self) -> str:
        return self.event_type.value.removesuffix("_violation")


class StakeholderProfile(BaseModel):
    role: NegotiationRole
    objectives: list[str]
    priorities: dict[str, float]
    flexibility_margins: dict[str, float]
    context_description: str
    tone: str = "neutral"


class ZOPA(BaseModel):
    feasible_range_per_metric: dict[str, tuple[float, float]]
    units: dict[str, str] = Field(default_factory=dict)
    current_targets: dict[str, float] = Field(default_factory=dict)
    low_is_better: dict[str, bool] = Field(default_factory=dict)
    description: str


class Proposal(BaseModel):
    round_number: int
    role: NegotiationRole
    content: str
    structured_adjustments: dict[str, float] | None = None
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class RenegotiationClause(BaseModel):
    clause_text: str


class Workflow(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex[:12])
    status: RenegotiationStatus = RenegotiationStatus.PENDING
    violation: Violation | None = None
    sla_id: str | None = None
    max_rounds: int = 10
    client_form: BaseModel | None = None
    provider_form: BaseModel | None = None
    client_profile: StakeholderProfile | None = None
    provider_profile: StakeholderProfile | None = None
    zopa: ZOPA | None = None
    proposals: list[Proposal] = Field(default_factory=list)
    current_round: int = 0
    rc: RenegotiationClause | None = None
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now().isoformat())
