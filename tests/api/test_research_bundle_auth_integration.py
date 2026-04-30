from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.application.research_integrity import build_semantic_research_gate_artifact
from tests.application.test_research_gate_artifact import _verified_proposal


def test_extracted_bundle_routes_require_token_and_accept_valid_payload(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "bundle-secret")
    client = TestClient(app)

    proposal = _verified_proposal()
    gate_artifact = build_semantic_research_gate_artifact(proposal)
    headers = {"Authorization": "Bearer bundle-secret"}

    readiness_body = {
        "proposal": proposal.model_dump(mode="json"),
        "gate_artifact": gate_artifact.model_dump(mode="json"),
        "require_gate_artifact": True,
    }

    blocked = client.post("/research/semantic-adjudication-readiness", json=readiness_body)
    assert blocked.status_code == 401

    readiness = client.post("/research/semantic-adjudication-readiness", json=readiness_body, headers=headers)
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["schema_version"] == "semantic_adjudication_readiness/v1"
    assert readiness_payload["ready_for_adjudication"] is True

    handoff = client.post("/research/semantic-adjudication-handoff/artifact", json=readiness_body, headers=headers)
    assert handoff.status_code == 200
    handoff_payload = handoff.json()
    assert handoff_payload["schema_version"] == "semantic_adjudication_handoff_artifact/v1"

    bundle_body = {
        "proposal": proposal.model_dump(mode="json"),
        "gate_artifact": gate_artifact.model_dump(mode="json"),
        "handoff_artifact": handoff_payload,
        "require_gate_artifact": True,
    }
    bundle = client.post("/research/semantic-adjudication-bundle", json=bundle_body, headers=headers)
    assert bundle.status_code == 200
    bundle_payload = bundle.json()
    assert bundle_payload["schema_version"] == "semantic_adjudication_bundle/v1"

    verify = client.post(
        "/research/semantic-adjudication-bundle/verify",
        json={"bundle": bundle_payload, "proposal": proposal.model_dump(mode="json")},
        headers=headers,
    )
    assert verify.status_code == 200
    verify_payload = verify.json()
    assert verify_payload["schema_version"] == "semantic_adjudication_bundle_verification/v1"
    assert verify_payload["verified"] is True
