from pydantic import BaseModel, Field


class CreateWorkflowRequest(BaseModel):
    event_type: str = "latency_violation"
    observed_value: float
    agreed_value: float
    unit: str = ""
    time_to_repair_seconds: int | None = None
    description: str = ""
    max_rounds: int = 10


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
    current_round: int
    max_rounds: int
    proposals: list[dict] = Field(default_factory=list)
    rc: dict | None = None
    created_at: str
    updated_at: str


class ValidateRCRequest(BaseModel):
    accepted: bool
    feedback: str = ""
