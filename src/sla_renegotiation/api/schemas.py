from pydantic import BaseModel, Field

from sla_renegotiation.domain.models import StakeholderProfile


class CreateWorkflowRequest(BaseModel):
    sla_id: str
    max_rounds: int = 10
    metric_weights: dict[str, float] | None = None


class SetProfileRequest(BaseModel):
    objectives: list[str]
    priorities: dict[str, float]
    flexibility_margins: dict[str, float]
    context_description: str
    tone: str = "neutral"


class GenerateProfileRequest(BaseModel):
    context: str


class EvaluateProfileRequest(BaseModel):
    context: str
    profile: StakeholderProfile


class ProfileEvaluationResponse(BaseModel):
    intent_faithfulness_score: float
    intent_faithfulness_reasoning: str
    information_completeness_score: float
    information_completeness_reasoning: str
    non_fabrication_score: float
    non_fabrication_reasoning: str
    clarity_and_usability_score: float
    clarity_and_usability_reasoning: str
    overall_score: float


class SimulateViolationRequest(BaseModel):
    event_type: str
    observed_value: float


class SLODefinitionResponse(BaseModel):
    metric: str
    target_value: float
    unit: str
    description: str
    event_type: str
    time_to_repair: int


class SLOConfigResponse(BaseModel):
    metric: str
    unit: str
    agreed_value: float
    description: str
    event_type: str
    time_to_repair: int


class SLASummaryResponse(BaseModel):
    id: str
    name: str
    description: str
    slo_count: int


class SLADetailResponse(BaseModel):
    id: str
    name: str
    description: str
    slos: list[SLODefinitionResponse]


class WorkflowResponse(BaseModel):
    id: str
    status: str
    sla_id: str | None = None
    current_round: int
    max_rounds: int
    proposals: list[dict[str, object]] = Field(default_factory=list)
    rc: dict[str, object] | None = None
    client_profile: dict[str, object] | None = None
    provider_profile: dict[str, object] | None = None
    zopa: dict[str, object] | None = None
    violation: dict[str, object] | None = None
    created_at: str
    updated_at: str


class ValidateRCRequest(BaseModel):
    accepted: bool
    feedback: str = ""


class SLASLOConfigResponse(BaseModel):
    metric: str
    unit: str
    agreed_value: float
    description: str
    event_type: str
    time_to_repair: int
