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
