from sla_renegotiation.domain.enums import EventType
from sla_renegotiation.domain.models import SLODefinition, StakeholderProfile
from sla_renegotiation.zopa.calculator import compute_zopa
from tests.conftest import sample_client_profile, sample_provider_profile  # noqa: F401


def _slo(metric: str, target: float, unit: str = "") -> dict[str, SLODefinition]:
    event_map = {
        "latency": EventType.LATENCY_VIOLATION,
        "availability": EventType.AVAILABILITY_VIOLATION,
        "cost": EventType.COST_OVERAGE,
    }
    return {
        metric: SLODefinition(
            metric=metric,
            target_value=target,
            unit=unit,
            description="",
            event_type=event_map.get(metric, EventType.LATENCY_VIOLATION),
        )
    }


def test_zopa_has_overlapping_metrics(sample_client_profile, sample_provider_profile):  # noqa: F811
    slo_defs = _slo("latency", 100.0, "ms") | _slo("availability", 99.9, "%")
    zopa = compute_zopa(
        sample_client_profile,
        sample_provider_profile,
        slo_definitions=slo_defs,
    )
    assert len(zopa.feasible_range_per_metric) > 0
    assert zopa.units.get("latency") == "ms"
    assert "availability" in zopa.current_targets


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
    zopa = compute_zopa(
        client,
        provider,
        slo_definitions=_slo("latency", 100.0),
    )
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
    assert lo == 300.0
    assert hi == 500.0


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
    assert lo == 400.0
    assert hi == 500.0
