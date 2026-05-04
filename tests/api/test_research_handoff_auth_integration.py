from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType


def _validator_handoff_evidence_payload() -> dict[str, object]:
    evidence = Evidence(
        evidence_id="semantic-release-handoff-certificate-evidence-route-smoke",
        experiment_id="EXP-HANDOFF-ROUTE-AUTH-001",
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        payload={"schema_version": "semantic_release_handoff_certificate_evidence/v1"},
        source_module="tests.api.research_handoff_auth_integration",
        checksum="f" * 64,
    )
    return evidence.model_dump(mode="json")


def test_extracted_handoff_route_requires_token_and_accepts_valid_payload(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "handoff-secret")
    client = TestClient(app)
    body = {"evidence": _validator_handoff_evidence_payload()}

    blocked = client.post("/research/semantic-adjudication-bundle/validator-handoff-packet", json=body)
    assert blocked.status_code == 401

    response = client.post(
        "/research/semantic-adjudication-bundle/validator-handoff-packet",
        json=body,
        headers={"Authorization": "Bearer handoff-secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "semantic_validator_handoff_packet/v1"
    assert payload["experiment_id"] == "EXP-HANDOFF-ROUTE-AUTH-001"
    assert payload["evidence_id"] == "semantic-release-handoff-certificate-evidence-route-smoke"
