from fastapi.testclient import TestClient

from sla_renegotiation.api.server import app
from sla_renegotiation.storage.in_memory import WorkflowStore

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_create_and_get_workflow():
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "pending"
    assert data["max_rounds"] == 10
    assert data["sla_id"] == "basic-api"

    wf_id = data["id"]
    resp = client.get(f"/workflows/{wf_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == wf_id


def test_get_workflow_slos():
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.get(f"/workflows/{wf_id}/slos")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) > 0
    metrics = {s["metric"] for s in data}
    assert "latency" in metrics


def test_set_batnas():
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    resp = client.post(
        f"/workflows/{wf_id}/batnas",
        json={
            "client_batnas": {
                "latency": 130.0,
                "availability": 99.0,
                "throughput": 800.0,
                "error_rate": 0.5,
            },
            "provider_batnas": {
                "latency": 110.0,
                "availability": 99.5,
                "throughput": 1200.0,
                "error_rate": 1.5,
            },
        },
    )
    assert resp.status_code == 200

    # Verify SLOs now have BATNAs
    resp = client.get(f"/workflows/{wf_id}/slos")
    data = resp.json()
    latency_slo = next(s for s in data if s["metric"] == "latency")
    assert latency_slo["client_batna"] == 130.0
    assert latency_slo["provider_batna"] == 110.0


def test_set_profiles():
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    profile = {
        "objectives": ["Reduce latency"],
        "priorities": {"latency": 0.6, "availability": 0.4},
        "flexibility_margins": {"latency": 0.2, "availability": 0.1},
        "context_description": "Gaming platform",
        "tone": "collaborative",
    }

    resp = client.post(f"/workflows/{wf_id}/profiles/client", json=profile)
    assert resp.status_code == 200
    assert resp.json()["client_profile"] is not None

    resp = client.post(
        f"/workflows/{wf_id}/profiles/provider",
        json={
            **profile,
            "context_description": "Provider with constraints",
        },
    )
    assert resp.status_code == 200
    assert resp.json()["provider_profile"] is not None


def test_simulate_violation():
    resp = client.post("/workflows", json={"sla_id": "basic-api"})
    wf_id = resp.json()["id"]

    # Set BATNAs first
    client.post(
        f"/workflows/{wf_id}/batnas",
        json={
            "client_batnas": {
                "latency": 130.0,
                "availability": 99.0,
                "throughput": 800.0,
                "error_rate": 0.5,
            },
            "provider_batnas": {
                "latency": 110.0,
                "availability": 99.5,
                "throughput": 1200.0,
                "error_rate": 1.5,
            },
        },
    )

    resp = client.post(
        f"/workflows/{wf_id}/violation",
        json={"event_type": "latency_violation", "observed_value": 200.0},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["violation"] is not None
    assert data["violation"]["event_type"] == "latency_violation"
    assert data["violation"]["observed_value"] == 200.0
    # agreed_value should be auto-detected from SLO
    assert data["violation"]["agreed_value"] is not None


def test_workflow_not_found():
    resp = client.get("/workflows/nonexistent")
    assert resp.status_code == 404


def test_full_flow_e2e():
    # Create workflow
    resp = client.post("/workflows", json={"sla_id": "basic-api", "max_rounds": 10})
    wf_id = resp.json()["id"]
    assert resp.status_code == 200

    # Set BATNAs
    resp = client.post(
        f"/workflows/{wf_id}/batnas",
        json={
            "client_batnas": {
                "latency": 150.0,
                "availability": 99.0,
                "throughput": 800.0,
                "error_rate": 0.5,
            },
            "provider_batnas": {
                "latency": 100.0,
                "availability": 99.5,
                "throughput": 1200.0,
                "error_rate": 2.0,
            },
        },
    )
    assert resp.status_code == 200

    # Set profiles
    client_profile = {
        "objectives": ["Reduce latency"],
        "priorities": {"latency": 0.6, "availability": 0.4},
        "flexibility_margins": {"latency": 0.2, "availability": 0.1},
        "context_description": "Gaming platform",
        "tone": "collaborative",
    }
    resp = client.post(f"/workflows/{wf_id}/profiles/client", json=client_profile)
    assert resp.status_code == 200

    provider_profile = {
        "objectives": ["Control costs"],
        "priorities": {"latency": 0.3, "cost": 0.7},
        "flexibility_margins": {"latency": 0.15, "cost": 0.2},
        "context_description": "Provider constraints",
        "tone": "formal",
    }
    resp = client.post(f"/workflows/{wf_id}/profiles/provider", json=provider_profile)
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
