from collections.abc import Sequence
from typing import Annotated, TypedDict

from langgraph.graph import add_messages

from sla_renegotiation.domain.enums import RenegotiationStatus
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile


class NegotiationState(TypedDict):
    workflow_id: str
    client_profile: StakeholderProfile
    provider_profile: StakeholderProfile
    zopa: ZOPA
    proposals: Annotated[Sequence[Proposal], add_messages]
    current_round: int
    max_rounds: int
    status: RenegotiationStatus
    next_role: str
    agreement_reached: bool
    violated_metric: str
