from fastapi.testclient import TestClient

from sla_renegotiation.api.server import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_workflow():
    resp = client.post(
        "/workflows",
        json={
            "event_type": "latency_violation",
            "observed_value": 150.0,
            "agreed_value": 100.0,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "context_gathering"
    assert data["max_rounds"] == 10

    wf_id = data["id"]
    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id


def test_submit_client_context():
    resp = client.post(
        "/workflows",
        json={
            "event_type": "latency_violation",
            "observed_value": 200.0,
            "agreed_value": 100.0,
            "unit": "ms",
        },
    )
    wf_id = resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/context/client",
        json={
            "business_context": "Gaming platform",
            "objectives": ["Reduce latency"],
            "priorities": {"latency": 0.6, "availability": 0.4},
            "flexibility_margins": {"latency": 0.2, "availability": 0.1},
            "constraints": ["Max 200ms"],
            "batna": 150.0,
        },
    )
    assert resp.status_code == 200


def test_workflow_not_found():
    resp = client.get("/workflows/nonexistent")
    assert resp.status_code == 404
