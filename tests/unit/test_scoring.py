from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ZOPA, Proposal, StakeholderProfile
from sla_renegotiation.negotiation.scoring import compute_utility_score


def _profile(
    role: NegotiationRole, priorities: dict[str, float] | None = None
) -> StakeholderProfile:
    return StakeholderProfile(
        role=role,
        objectives=["test"],
        priorities=priorities or {"latency": 1.0},
        flexibility_margins={"latency": 0.1},
        context_description="test",
        tone="neutral",
    )


def _zopa(
    ranges: dict[str, tuple[float, float]] | None = None,
    low_is_better: dict[str, bool] | None = None,
) -> ZOPA:
    return ZOPA(
        feasible_range_per_metric=ranges or {"latency": (50.0, 150.0)},
        low_is_better=low_is_better or {"latency": True},
        description="test",
        units={"latency": "ms"},
    )


def _proposal(
    adjustments: dict[str, float] | None = None,
) -> Proposal:
    return Proposal(
        round_number=1,
        role=NegotiationRole.CLIENT,
        content="test proposal",
        structured_adjustments=adjustments,
    )


def test_no_adjustments_returns_maximum() -> None:
    proposal = _proposal(adjustments=None)
    profile = _profile(NegotiationRole.PROVIDER)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.PROVIDER)
    assert score == 1.0


def test_empty_adjustments_returns_maximum() -> None:
    proposal = _proposal(adjustments={})
    profile = _profile(NegotiationRole.PROVIDER)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.PROVIDER)
    assert score == 1.0


def test_client_ideal_is_low_for_low_is_better() -> None:
    proposal = _proposal(adjustments={"latency": 50.0})
    profile = _profile(NegotiationRole.CLIENT)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 1.0


def test_client_penalized_for_high_value_when_low_is_better() -> None:
    proposal = _proposal(adjustments={"latency": 150.0})
    profile = _profile(NegotiationRole.CLIENT)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 0.0


def test_provider_ideal_is_high_for_low_is_better() -> None:
    proposal = _proposal(adjustments={"latency": 150.0})
    profile = _profile(NegotiationRole.PROVIDER)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.PROVIDER)
    assert score == 1.0


def test_provider_penalized_for_low_value_when_low_is_better() -> None:
    proposal = _proposal(adjustments={"latency": 50.0})
    profile = _profile(NegotiationRole.PROVIDER)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.PROVIDER)
    assert score == 0.0


def test_mid_range_score() -> None:
    proposal = _proposal(adjustments={"latency": 100.0})
    profile = _profile(NegotiationRole.CLIENT)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 0.5


def test_weighted_multi_metric() -> None:
    profile = _profile(
        NegotiationRole.CLIENT,
        priorities={"latency": 0.7, "availability": 0.3},
    )
    zopa = _zopa(
        ranges={"latency": (50.0, 150.0), "availability": (99.0, 99.9)},
        low_is_better={"latency": True, "availability": False},
    )
    proposal = _proposal(adjustments={"latency": 50.0, "availability": 99.9})
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 1.0


def test_zero_weight_metric_ignored() -> None:
    profile = _profile(
        NegotiationRole.CLIENT,
        priorities={"latency": 1.0, "availability": 0.0},
    )
    zopa = _zopa(
        ranges={"latency": (50.0, 150.0), "availability": (99.0, 99.9)},
        low_is_better={"latency": True, "availability": False},
    )
    proposal = _proposal(adjustments={"latency": 50.0, "availability": 0.0})
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 1.0


def test_clamping_prevents_out_of_range() -> None:
    proposal = _proposal(adjustments={"latency": 999.0})
    profile = _profile(NegotiationRole.CLIENT)
    zopa = _zopa()
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 0.0


def test_high_is_better_client() -> None:
    zopa = _zopa(
        ranges={"throughput": (100.0, 500.0)},
        low_is_better={"throughput": False},
    )
    profile = _profile(NegotiationRole.CLIENT, priorities={"throughput": 1.0})
    proposal = _proposal(adjustments={"throughput": 500.0})
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.CLIENT)
    assert score == 1.0


def test_high_is_better_provider() -> None:
    zopa = _zopa(
        ranges={"throughput": (100.0, 500.0)},
        low_is_better={"throughput": False},
    )
    profile = _profile(NegotiationRole.PROVIDER, priorities={"throughput": 1.0})
    proposal = _proposal(adjustments={"throughput": 100.0})
    score = compute_utility_score(proposal, profile, zopa, NegotiationRole.PROVIDER)
    assert score == 1.0
