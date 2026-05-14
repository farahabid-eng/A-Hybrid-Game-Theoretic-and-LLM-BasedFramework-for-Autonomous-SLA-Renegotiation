from pydantic import BaseModel, Field


class CreateWorkflowRequest(BaseModel):
    event_type: str = "latency_violation"
    observed_value: float
    agreed_value: float | None = None
    unit: str = ""
    sla_id: str | None = None
    time_to_repair: int | None = None
    description: str = ""
    max_rounds: int = 10


class SLODefinitionResponse(BaseModel):
    metric: str
    target_value: float
    unit: str
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


class SubmitClientFormRequest(BaseModel):
    business_context: str
    objectives: list[str]
    priorities: dict[str, float]
    flexibility_margins: dict[str, float]
    constraints: list[str]
    batna: float
    tone: str = "neutral"


class SubmitProviderFormRequest(BaseModel):
    resource_limitations: list[str]
    operational_constraints: list[str]
    priorities: dict[str, float]
    flexibility_margins: dict[str, float]
    cost_considerations: str
    batna: float


class WorkflowResponse(BaseModel):
    id: str
    status: str
    sla_id: str | None = None
    current_round: int
    max_rounds: int
    proposals: list[dict[str, object]] = Field(default_factory=list)
    rc: dict[str, object] | None = None
    created_at: str
    updated_at: str


class ValidateRCRequest(BaseModel):
    accepted: bool
    feedback: str = ""
