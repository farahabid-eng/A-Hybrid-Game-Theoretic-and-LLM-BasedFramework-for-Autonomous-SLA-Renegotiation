from unittest.mock import MagicMock, patch

from sla_renegotiation.domain.enums import NegotiationRole
from sla_renegotiation.domain.models import ProfileEvaluationResult, StakeholderProfile
from sla_renegotiation.profiles.evaluator import evaluate_profile


def test_evaluate_profile_success() -> None:
    mock_result = ProfileEvaluationResult(
        intent_faithfulness_score=90.0,
        intent_faithfulness_reasoning="Good alignment with client goals.",
        information_completeness_score=85.0,
        information_completeness_reasoning="Most information is present.",
        non_fabrication_score=95.0,
        non_fabrication_reasoning="No unsupported claims detected.",
        clarity_and_usability_score=100.0,
        clarity_and_usability_reasoning="Very clear structure.",
    )

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result

    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    profile = StakeholderProfile(
        role=NegotiationRole.CLIENT,
        objectives=["Restore latency below 100ms"],
        priorities={"latency": 1.0},
        flexibility_margins={"latency": 0.1},
        context_description="Gaming customer requiring sub-100ms latency.",
        tone="collaborative",
    )

    with patch(
        "sla_renegotiation.profiles.evaluator.build_model", return_value=mock_model
    ) as mock_build:
        res = evaluate_profile(
            context="Our main objective is restoring latency below 100ms.",
            role=NegotiationRole.CLIENT,
            profile=profile,
        )

        mock_build.assert_called_once_with("judge", temperature=0.0)
        mock_model.with_structured_output.assert_called_once_with(ProfileEvaluationResult)

        assert res.intent_faithfulness_score == 90.0
        assert res.overall_score == 92.5
