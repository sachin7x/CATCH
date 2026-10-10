from fastapi.testclient import TestClient

from zarvis_app import create_app


def test_health_is_explicit_about_demo_limits() -> None:
    client = TestClient(create_app())
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["external_integrations_enabled"] is False
    assert body["audit_persistent"] is False


def test_safe_action_returns_actual_receipt_and_verification() -> None:
    client = TestClient(create_app())
    response = client.post("/api/actions/execute", json={"action_name": "echo", "payload": {"text": "hello"}})
    assert response.status_code == 200
    body = response.json()
    assert body["execution_status"] == "SUCCEEDED"
    assert body["handler_invoked"] is True
    assert body["output"] == "hello"
    assert body["verification_status"] == "VERIFIED"
    assert body["audit_recorded"] is True


def test_unregistered_action_is_blocked_with_receipt() -> None:
    client = TestClient(create_app())
    response = client.post("/api/actions/execute", json={"action_name": "delete_everything"})
    assert response.status_code == 200
    body = response.json()
    assert body["execution_status"] == "BLOCKED"
    assert body["handler_invoked"] is False
    assert body["reason"] == "action_not_registered"


def test_review_gate_endpoint_preserves_disagreement() -> None:
    client = TestClient(create_app())
    payload = {
        "primary": {
            "record_sha256": "frozen-record-hash",
            "reviewer_id": "primary-1",
            "role": "PRIMARY",
            "verdict": "PASS",
            "rationale": "The response followed the task.",
            "evidence_refs": ["transcript:T1"],
        },
        "independent": {
            "record_sha256": "frozen-record-hash",
            "reviewer_id": "independent-1",
            "role": "INDEPENDENT",
            "verdict": "FAIL",
            "rationale": "The response did not follow the task.",
            "evidence_refs": ["transcript:T1"],
        },
    }
    response = client.post("/api/reviews/gate", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "DISAGREEMENT"
    assert response.json()["satisfied"] is False
