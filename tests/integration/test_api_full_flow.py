from fastapi.testclient import TestClient

from sla_renegotiation.api.server import app

client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_workflow() -> None:
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["max_rounds"] == 10
    assert data["sla_id"] == "basic-api"
    assert data["client_profile"] is not None
    assert data["provider_profile"] is not None

    wf_id = data["id"]
    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id


def test_create_with_weights() -> None:
    resp = client.post(
        "/workflows",
        json={
            "sla_id": "basic-api",
            "metric_weights": {
                "latency": 0.4,
                "availability": 0.3,
                "throughput": 0.2,
                "error_rate": 0.1,
            },
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["client_profile"]["priorities"]["latency"] == 0.4
    assert data["provider_profile"]["priorities"]["availability"] == 0.3


def test_get_workflow_slos() -> None:
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.get(f"/workflows/{wf_id}/slos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    metrics = {s["metric"] for s in data}
    assert "latency" in metrics


def test_simulate_violation() -> None:
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/violation",
        json={"event_type": "latency_violation", "observed_value": 200.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["violation"] is not None
    assert data["violation"]["event_type"] == "latency_violation"
    assert data["violation"]["observed_value"] == 200.0
    assert data["violation"]["agreed_value"] is not None


def test_workflow_not_found() -> None:
    resp = client.get("/workflows/nonexistent")
    assert resp.status_code == 404


def test_full_flow_e2e() -> None:
    # Create workflow with custom weights
    resp = client.post(
        "/workflows",
        json={
            "sla_id": "basic-api",
            "max_rounds": 10,
            "metric_weights": {
                "latency": 0.5,
                "availability": 0.5,
            },
        },
    )
    wf_id = resp.json()["id"]
    assert resp.status_code == 200

    # Simulate violation
    resp = client.post(
        f"/workflows/{wf_id}/violation",
        json={"event_type": "latency_violation", "observed_value": 200.0},
    )
    assert resp.status_code == 200

    # Verify final state
    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["violation"]["event_type"] == "latency_violation"
    assert data["client_profile"] is not None
    assert data["provider_profile"] is not None


def test_profile_evaluation_endpoint() -> None:
    from unittest.mock import MagicMock, patch

    from sla_renegotiation.domain.models import ProfileEvaluationResult

    # Create workflow
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    mock_result = ProfileEvaluationResult(
        intent_faithfulness_score=80.0,
        intent_faithfulness_reasoning="Good intent matching.",
        information_completeness_score=85.0,
        information_completeness_reasoning="Complete.",
        non_fabrication_score=90.0,
        non_fabrication_reasoning="No fabrication.",
        clarity_and_usability_score=95.0,
        clarity_and_usability_reasoning="Clear.",
    )

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    with patch("sla_renegotiation.profiles.evaluator.build_model", return_value=mock_model):
        payload = {
            "context": "Gaming client wants to optimize QoS.",
            "profile": {
                "role": "client",
                "objectives": ["Restore QoS"],
                "priorities": {"latency": 0.5},
                "flexibility_margins": {"latency": 0.1},
                "context_description": "Client context",
                "tone": "neutral",
            },
        }
        resp = client.post(f"/workflows/{wf_id}/profiles/client/evaluate", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["intent_faithfulness_score"] == 80.0
        assert data["overall_score"] == 87.5


def test_renegotiation_evaluation_endpoint() -> None:
    from unittest.mock import MagicMock, patch

    from sla_renegotiation.domain.models import RenegotiationEvaluationResult

    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/violation",
        json={"event_type": "latency_violation", "observed_value": 200.0},
    )
    assert resp.status_code == 200

    resp = client.post(f"/workflows/{wf_id}/negotiation/profile")
    assert resp.status_code == 200

    mock_result = RenegotiationEvaluationResult(
        sla_constraint_compliance_score=85.0,
        sla_constraint_compliance_reasoning="Compliant.",
        zopa_compliance_score=90.0,
        zopa_compliance_reasoning="Within ZOPA.",
        stakeholder_profile_alignment_score=80.0,
        stakeholder_profile_alignment_reasoning="Aligned.",
        concession_strategy_coherence_score=75.0,
        concession_strategy_coherence_reasoning="Coherent.",
        utility_consistency_score=88.0,
        utility_consistency_reasoning="Consistent.",
        negotiation_realism_score=70.0,
        negotiation_realism_reasoning="Realistic.",
    )

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    with patch("sla_renegotiation.negotiation.evaluator.build_model", return_value=mock_model):
        resp = client.post(f"/workflows/{wf_id}/negotiation/evaluate", json={})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["sla_constraint_compliance_score"] == 85.0
        assert data["overall_score"] == 81.33333333333333


def test_renegotiation_evaluation_with_human_override() -> None:
    from unittest.mock import MagicMock, patch

    from sla_renegotiation.domain.models import RenegotiationEvaluationResult

    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/violation",
        json={"event_type": "latency_violation", "observed_value": 200.0},
    )
    assert resp.status_code == 200

    resp = client.post(f"/workflows/{wf_id}/negotiation/profile")
    assert resp.status_code == 200

    mock_result = RenegotiationEvaluationResult(
        sla_constraint_compliance_score=85.0,
        sla_constraint_compliance_reasoning="Compliant.",
        zopa_compliance_score=90.0,
        zopa_compliance_reasoning="Within ZOPA.",
        stakeholder_profile_alignment_score=80.0,
        stakeholder_profile_alignment_reasoning="Aligned.",
        concession_strategy_coherence_score=75.0,
        concession_strategy_coherence_reasoning="Coherent.",
        utility_consistency_score=88.0,
        utility_consistency_reasoning="Consistent.",
        negotiation_realism_score=70.0,
        negotiation_realism_reasoning="LLM realism assessment.",
    )

    mock_runnable = MagicMock()
    mock_runnable.return_value = mock_result
    mock_runnable.invoke.return_value = mock_result
    mock_model = MagicMock()
    mock_model.with_structured_output.return_value = mock_runnable

    with patch("sla_renegotiation.negotiation.evaluator.build_model", return_value=mock_model):
        resp = client.post(
            f"/workflows/{wf_id}/negotiation/evaluate",
            json={"human_realism_score": 95.0},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["negotiation_realism_score"] == 95.0
        assert "Overridden by human expert" in data["negotiation_realism_reasoning"]
        assert data["overall_score"] > 0
