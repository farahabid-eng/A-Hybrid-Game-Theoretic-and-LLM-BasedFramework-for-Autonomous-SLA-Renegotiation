from sla_renegotiation.domain.enums import EventType, RenegotiationStatus
from sla_renegotiation.domain.models import Violation, Workflow


def test_violation_defaults() -> None:
    v = Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=200.0,
        agreed_value=100.0,
        unit="ms",
    )
    assert v.description == ""


def test_workflow_auto_id() -> None:
    w1 = Workflow()
    w2 = Workflow()
    assert w1.id != w2.id


def test_workflow_default_status() -> None:
    w = Workflow()
    assert w.status == RenegotiationStatus.PENDING
