import pytest

from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import StakeholderProfile
from sla_renegotiation.zopa.calculator import compute_zopa
from tests.conftest import sample_client_profile, sample_provider_profile  # noqa: F401


def test_zopa_has_overlapping_metrics(sample_client_profile, sample_provider_profile):  # noqa: F811
    zopa = compute_zopa(sample_client_profile, sample_provider_profile)
    assert len(zopa.feasible_range_per_metric) > 0


def test_zopa_no_overlap():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": -0.5},
        constraints=[],
        batna=None,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.1},
        constraints=[],
        batna=None,
        context_description="",
    )
    zopa = compute_zopa(client, provider)
    assert len(zopa.feasible_range_per_metric) == 0


def test_zopa_client_batna_caps_upper_for_low_is_better():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.3},
        constraints=[],
        batna=500.0,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.3},
        constraints=[],
        batna=300.0,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=300.0,
    )
    lo, hi = zopa.feasible_range_per_metric["latency"]
    assert lo == 1.0
    assert hi == round(500.0 / 300.0, 4)


def test_zopa_batna_interval_takes_precedence_over_flex_margins():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.1},
        constraints=[],
        batna=500.0,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={"latency": 0.1},
        constraints=[],
        batna=400.0,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=300.0,
    )
    lo, hi = zopa.feasible_range_per_metric["latency"]
    assert lo == round(400.0 / 300.0, 4)
    assert hi == round(500.0 / 300.0, 4)
