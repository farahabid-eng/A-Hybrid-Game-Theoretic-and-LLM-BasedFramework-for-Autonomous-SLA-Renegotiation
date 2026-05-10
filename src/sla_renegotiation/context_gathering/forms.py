from pydantic import BaseModel, Field


class ClientForm(BaseModel):
    business_context: str = Field(description="Description of the business motivating renegotiation")
    objectives: list[str] = Field(description="Specific objectives for renegotiation")
    priorities: dict[str, float] = Field(description="Metric priority weights summing to 1.0")
    flexibility_margins: dict[str, float] = Field(description="Acceptable deviation per metric")
    constraints: list[str] = Field(description="Non-negotiable constraints")
    batna: float = Field(description="Walk-away absolute value for the violated metric")
    tone: str = Field(default="neutral", description="Negotiation tone (aggressive, collaborative, diplomatic, urgent, etc.)")


class ProviderForm(BaseModel):
    resource_limitations: list[str] = Field(description="Infrastructure or resource constraints")
    operational_constraints: list[str] = Field(description="Operational limitations")
    priorities: dict[str, float] = Field(description="Metric priority weights summing to 1.0")
    flexibility_margins: dict[str, float] = Field(description="Acceptable deviation per metric")
    cost_considerations: str = Field(description="Cost structure and constraints")
    batna: float = Field(description="Walk-away absolute value for the violated metric")
