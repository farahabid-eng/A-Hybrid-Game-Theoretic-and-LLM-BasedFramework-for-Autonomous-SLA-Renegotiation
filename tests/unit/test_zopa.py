from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import Proposal, SLODefinition, StakeholderProfile, ZOPA
from sla_renegotiation.zopa.calculator import compute_zopa, narrow_zopa
from tests.conftest import sample_client_profile, sample_provider_profile  # noqa: F401


def _make_zopa(
    range_map: dict[str, tuple[float, float]],
    low_better: dict[str, bool] | None = None,
) -> ZOPA:
    return ZOPA(
        feasible_range_per_metric=range_map,
        low_is_better=low_better or {m: True for m in range_map},
        description="test",
    )


def _proposal(role: NegotiationRole, adjustments: dict[str, float]) -> Proposal:
    return Proposal(
        round_number=1,
        role=role,
        content="test",
        structured_adjustments=adjustments,
    )


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
            time_to_repair=5,
        )
    }


def test_zopa_requires_both_batnas():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=None,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=110.0,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=100.0,
    )
    assert len(zopa.feasible_range_per_metric) == 0
    assert "BATNA" in zopa.description


def test_zopa_low_is_better():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=130.0,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=110.0,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=100.0,
    )
    lo, hi = zopa.feasible_range_per_metric["latency"]
    assert lo == 110.0
    assert hi == 130.0


def test_zopa_high_is_better():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=99.0,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=99.9,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.AVAILABILITY_VIOLATION,
        agreed_value=99.5,
    )
    lo, hi = zopa.feasible_range_per_metric["availability"]
    assert lo == 99.0
    assert hi == 99.9


def test_zopa_no_overlap():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=100.0,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=200.0,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=150.0,
    )
    assert len(zopa.feasible_range_per_metric) == 0


def test_zopa_no_violation(sample_client_profile, sample_provider_profile):  # noqa: F811
    zopa = compute_zopa(
        sample_client_profile,
        sample_provider_profile,
        violated_event_type=None,
    )
    assert len(zopa.feasible_range_per_metric) == 0


def test_zopa_only_violated_metric(sample_client_profile, sample_provider_profile):  # noqa: F811
    zopa = compute_zopa(
        sample_client_profile,
        sample_provider_profile,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=100.0,
        slo_definitions=_slo("latency", 100.0, "ms") | _slo("cost", 200.0, "$"),
    )
    assert list(zopa.feasible_range_per_metric.keys()) == ["latency"]
    assert "cost" not in zopa.feasible_range_per_metric


def test_zopa_sets_targets_and_units(sample_client_profile, sample_provider_profile):  # noqa: F811
    zopa = compute_zopa(
        sample_client_profile,
        sample_provider_profile,
        violated_event_type=EventType.LATENCY_VIOLATION,
        agreed_value=100.0,
        slo_definitions=_slo("latency", 100.0, "ms"),
    )
    assert zopa.current_targets.get("latency") == 100.0
    assert zopa.units.get("latency") == "ms"


def test_zopa_rounds_to_4_decimals():
    client = StakeholderProfile(
        role="client",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=130.12345,
        context_description="",
    )
    provider = StakeholderProfile(
        role="provider",
        objectives=[],
        priorities={},
        flexibility_margins={},
        constraints=[],
        batna=110.12345,
        context_description="",
    )
    zopa = compute_zopa(
        client,
        provider,
        violated_event_type=EventType.LATENCY_VIOLATION,
    )
    lo, hi = zopa.feasible_range_per_metric["latency"]
    assert round(lo, 4) == lo
    assert round(hi, 4) == hi


class TestNarrowZopa:
    def test_client_low_is_better_caps_upper(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.CLIENT, {"latency": 150.0})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (100.0, 150.0)

    def test_provider_low_is_better_raises_lower(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.PROVIDER, {"latency": 150.0})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (150.0, 200.0)

    def test_client_high_is_better_raises_lower(self):
        zopa = _make_zopa({"availability": (99.0, 99.99)}, {"availability": False})
        proposal = _proposal(NegotiationRole.CLIENT, {"availability": 99.9})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["availability"] == (99.9, 99.99)

    def test_provider_high_is_better_caps_upper(self):
        zopa = _make_zopa({"availability": (99.0, 99.99)}, {"availability": False})
        proposal = _proposal(NegotiationRole.PROVIDER, {"availability": 99.5})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["availability"] == (99.0, 99.5)

    def test_unmentioned_metric_unchanged(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.CLIENT, {})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (100.0, 200.0)

    def test_value_outside_range_clips_to_original(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.CLIENT, {"latency": 50.0})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (100.0, 100.0)

    def test_provider_outside_range_clips_to_original(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.PROVIDER, {"latency": 300.0})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (200.0, 200.0)

    def test_keeps_original_if_narrowing_crosses(self):
        zopa = _make_zopa({"latency": (100.0, 200.0)}, {"latency": True})
        proposal = _proposal(NegotiationRole.CLIENT, {"latency": 250.0})
        result = narrow_zopa(zopa, proposal)
        assert result.feasible_range_per_metric["latency"] == (100.0, 200.0)

    def test_preserves_units_and_targets(self):
        zopa = ZOPA(
            feasible_range_per_metric={"latency": (100.0, 200.0)},
            units={"latency": "ms"},
            current_targets={"latency": 150.0},
            low_is_better={"latency": True},
            description="test",
        )
        proposal = _proposal(NegotiationRole.CLIENT, {"latency": 120.0})
        result = narrow_zopa(zopa, proposal)
        assert result.units == {"latency": "ms"}
        assert result.current_targets == {"latency": 150.0}
        assert result.low_is_better == {"latency": True}
