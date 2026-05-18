from pydantic import BaseModel, Field


class CreateWorkflowRequest(BaseModel):
    sla_id: str
    max_rounds: int = 10


class SetBATNAsRequest(BaseModel):
    client_batnas: dict[str, float]
    provider_batnas: dict[str, float]


class SetProfileRequest(BaseModel):
    objectives: list[str]
    priorities: dict[str, float]
    flexibility_margins: dict[str, float]
    context_description: str
    tone: str = "neutral"


class GenerateProfileRequest(BaseModel):
    context: str


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
    client_batna: float | None = None
    provider_batna: float | None = None


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
    client_batna: float | None = None
    provider_batna: float | None = None
