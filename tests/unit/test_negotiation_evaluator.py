from unittest.mock import MagicMock, patch

from sla_renegotiation.domain.enums import EventType, NegotiationRole
from sla_renegotiation.domain.models import (
    ZOPA,
    Proposal,
    RenegotiationEvaluationResult,
    StakeholderProfile,
    Violation,
)
from sla_renegotiation.negotiation.evaluator import evaluate_renegotiation


def _make_result(**overrides: float) -> RenegotiationEvaluationResult:
    kwargs = {
        "sla_constraint_compliance_score": 85.0,
        "sla_constraint_compliance_reasoning": "Proposals stayed within SLA bounds.",
        "zopa_compliance_score": 90.0,
        "zopa_compliance_reasoning": "All offers within ZOPA.",
        "stakeholder_profile_alignment_score": 80.0,
        "stakeholder_profile_alignment_reasoning": "Profiles were respected.",
        "concession_strategy_coherence_score": 75.0,
        "concession_strategy_coherence_reasoning": "Gradual concessions.",
        "utility_consistency_score": 88.0,
        "utility_consistency_reasoning": "Consistent utility.",
        "negotiation_realism_score": 70.0,
        "negotiation_realism_reasoning": "Somewhat realistic.",
    }
    kwargs.update({k: v for k, v in overrides.items() if k in kwargs})
    return RenegotiationEvaluationResult(**kwargs)


def test_evaluate_renegotiation_success() -> None:
    mock_result = _make_result()

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result

    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    violation = Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=150.0,
        agreed_value=100.0,
        unit="ms",
    )
    zopa = ZOPA(
        feasible_range_per_metric={"latency": (100.0, 150.0)},
        description="Test ZOPA",
    )
    client_profile = StakeholderProfile(
        role=NegotiationRole.CLIENT,
        objectives=["Reduce latency"],
        priorities={"latency": 1.0},
        flexibility_margins={"latency": 0.1},
        context_description="Client context",
    )
    provider_profile = StakeholderProfile(
        role=NegotiationRole.PROVIDER,
        objectives=["Control costs"],
        priorities={"latency": 0.5, "cost": 0.5},
        flexibility_margins={"latency": 0.15, "cost": 0.2},
        context_description="Provider context",
    )
    proposals = [
        Proposal(round_number=1, role="client", content="Propose 120ms latency"),
        Proposal(round_number=1, role="provider", content="Propose 140ms latency"),
    ]

    with patch(
        "sla_renegotiation.negotiation.evaluator.build_model", return_value=mock_model
    ) as mock_build:
        result = evaluate_renegotiation(
            sla=None,
            slo_configs=[],
            violation=violation,
            zopa=zopa,
            client_profile=client_profile,
            provider_profile=provider_profile,
            proposals=proposals,
        )

        mock_build.assert_called_once_with("judge", temperature=0.0)
        mock_model.with_structured_output.assert_called_once_with(RenegotiationEvaluationResult)

        assert result.sla_constraint_compliance_score == 85.0
        assert result.overall_score == 81.33333333333333


def test_evaluate_renegotiation_partial_overrides() -> None:
    mock_result = _make_result()

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result

    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    violation = Violation(
        event_type=EventType.LATENCY_VIOLATION,
        observed_value=200.0,
        agreed_value=100.0,
        unit="ms",
    )
    zopa = ZOPA(
        feasible_range_per_metric={"latency": (100.0, 200.0)},
        description="Test ZOPA",
    )
    client_profile = StakeholderProfile(
        role=NegotiationRole.CLIENT,
        objectives=["Reduce latency"],
        priorities={"latency": 1.0},
        flexibility_margins={"latency": 0.1},
        context_description="Client context",
    )
    provider_profile = StakeholderProfile(
        role=NegotiationRole.PROVIDER,
        objectives=["Control costs"],
        priorities={"latency": 0.5, "cost": 0.5},
        flexibility_margins={"latency": 0.15, "cost": 0.2},
        context_description="Provider context",
    )

    with patch("sla_renegotiation.negotiation.evaluator.build_model", return_value=mock_model):
        result = evaluate_renegotiation(
            sla=None,
            slo_configs=[],
            violation=violation,
            zopa=zopa,
            client_profile=client_profile,
            provider_profile=provider_profile,
            proposals=[],
            rc=None,
        )

        assert result.negotiation_realism_score == 70.0
        assert result.overall_score == 81.33333333333333
