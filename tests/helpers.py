from datetime import datetime

from sla_renegotiation.domain.enums import EventType, RenegotiationStatus
from sla_renegotiation.domain.models import (
    Proposal,
    Violation,
    Workflow,
)


def build_sample_proposal(round_number: int = 1, role: str = "client") -> Proposal:
    return Proposal(
        round_number=round_number,
        role=role,
        content=f"Proposal from {role} in round {round_number}",
        structured_adjustments={"latency": 1.1},
        timestamp=datetime.now().isoformat(),
    )


def build_complete_workflow() -> Workflow:
    violation = Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=150.0,
        agreed_value=100.0,
        unit="ms",
    )
    return Workflow(violation=violation, status=RenegotiationStatus.CONTEXT_GATHERING)
