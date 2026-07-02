import pytest

from sla_renegotiation.context_gathering.forms import ClientForm, ProviderForm
from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import (
    StakeholderProfile,
    Violation,
    Workflow,
)
from sla_renegotiation.storage.in_memory import WorkflowStore


@pytest.fixture
def sample_violation():
    return Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=150.0,
        agreed_value=100.0,
        unit="ms",
        time_to_repair=300,
        description="P95 response time exceeded agreed threshold",
    )


@pytest.fixture
def sample_client_form():
    return ClientForm(
        business_context="Low-latency gaming platform",
        objectives=["Reduce latency", "Maintain availability"],
        priorities={"latency": 0.6, "availability": 0.4},
        flexibility_margins={"latency": 0.2, "availability": 0.1},
        constraints=["Cannot exceed 200ms p99"],
    )


@pytest.fixture
def sample_provider_form():
    return ProviderForm(
        resource_limitations=["Limited us-east capacity"],
        operational_constraints=["Maintenance window every 2 weeks"],
        priorities={"latency": 0.3, "cost": 0.7},
        flexibility_margins={"latency": 0.15, "cost": 0.2},
        cost_considerations="Hardware refresh increased costs 15%",
    )


@pytest.fixture
def sample_client_profile():
    return StakeholderProfile(
        role="client",
        objectives=["Reduce latency", "Maintain availability"],
        priorities={"latency": 0.6, "availability": 0.4},
        flexibility_margins={"latency": 0.2, "availability": 0.1},
        context_description="Low-latency gaming platform",
    )


@pytest.fixture
def sample_provider_profile():
    return StakeholderProfile(
        role="provider",
        objectives=["Control costs", "Optimize resource usage"],
        priorities={"latency": 0.3, "cost": 0.7},
        flexibility_margins={"latency": 0.15, "cost": 0.2},
        context_description="Provider with hardware refresh constraints",
    )


@pytest.fixture
def sample_zopa(sample_violation):
    from sla_renegotiation.zopa.calculator import compute_zopa

    return compute_zopa(
        violated_event_type=sample_violation.event_type,
        agreed_value=sample_violation.agreed_value,
    )


@pytest.fixture
def sample_workflow(sample_violation):
    return Workflow(
        violation=sample_violation,
        max_rounds=10,
    )


@pytest.fixture
def store():
    return WorkflowStore()
