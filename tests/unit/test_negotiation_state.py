from sla_renegotiation.negotiation.state import NegotiationState


def test_negotiation_state_structure(sample_client_profile, sample_provider_profile, sample_zopa):  # noqa: F811
    state = NegotiationState(
        workflow_id="test-123",
        client_profile=sample_client_profile,
        provider_profile=sample_provider_profile,
        zopa=sample_zopa,
        proposals=[],
        current_round=0,
        max_rounds=10,
        status="pending",
        next_role="client",
        agreement_reached=False,
    )
    assert state["workflow_id"] == "test-123"
    assert state["current_round"] == 0
    assert state["max_rounds"] == 10
