from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
)
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    return build_strategy_proposal(
        experiment_id="EXP-RELEASE-ROUTE-AUTH-001",
        strategy_name="ReleaseRouteAuthIntegrationSmoke",
        proposer_id="api-test",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
    )


def test_extracted_release_route_requires_token_and_accepts_valid_payload(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "release-secret")
    client = TestClient(app)

    proposal = _proposal()
    bundle = build_semantic_adjudication_bundle(proposal, require_gate_artifact=False)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    body = {
        "bundle": bundle.model_dump(mode="json"),
        "manifest": manifest.model_dump(mode="json"),
        "proposal": proposal.model_dump(mode="json"),
        "require_manifest": True,
    }

    blocked = client.post("/research/semantic-adjudication-bundle/release-preflight", json=body)
    assert blocked.status_code == 401

    response = client.post(
        "/research/semantic-adjudication-bundle/release-preflight",
        json=body,
        headers={"Authorization": "Bearer release-secret"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "semantic_adjudication_bundle_release_preflight/v1"
    assert payload["bundle_id"] == bundle.bundle_id
