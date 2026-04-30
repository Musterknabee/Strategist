from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_extracted_validator_submission_routes_require_configured_research_token(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "submission-secret")
    client = TestClient(app)

    blocked = client.post("/research/semantic-adjudication-bundle/validator-submission-packet", json={})
    assert blocked.status_code == 401
    assert blocked.json()["detail"] == "INVALID_RESEARCH_API_TOKEN"

    reached_route_validation = client.post(
        "/research/semantic-adjudication-bundle/validator-submission-packet",
        json={},
        headers={"Authorization": "Bearer submission-secret"},
    )
    assert reached_route_validation.status_code == 422


def test_extracted_validator_submission_route_accepts_valid_payload_with_token(monkeypatch) -> None:
    from strategy_validator.application.research_integrity import build_semantic_validator_ingress_acceptance_ledger

    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "submission-secret")
    client = TestClient(app)

    acceptance_ledger = build_semantic_validator_ingress_acceptance_ledger([])

    response = client.post(
        "/research/semantic-adjudication-bundle/validator-submission-packet",
        json={
            "acceptance_ledger": acceptance_ledger.model_dump(mode="json"),
            "submitted_by": "api-test",
            "submission_reason": "valid-payload-smoke",
        },
        headers={"Authorization": "Bearer submission-secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "semantic_validator_submission_packet/v1"
    assert payload["acceptance_ledger_id"] == acceptance_ledger.ledger_id
    assert payload["submitted_by"] == "api-test"
