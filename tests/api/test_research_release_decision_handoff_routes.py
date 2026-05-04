from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_release_capsule,
)
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _release_capsule_chain():
    proposal = build_strategy_proposal(
        experiment_id="EXP-RELEASE-DECISION-ROUTE-001",
        strategy_name="ReleaseDecisionRouteSmoke",
        proposer_id="api-test",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
    )
    bundle = build_semantic_adjudication_bundle(proposal, require_gate_artifact=False)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    index = build_semantic_adjudication_bundle_release_index(bundle, manifest=manifest, proposal=proposal)
    capsule = build_semantic_adjudication_release_capsule(index, bundle=bundle, manifest=manifest, proposal=proposal)
    return proposal, bundle, manifest, index, capsule


def test_release_decision_and_handoff_certificate_routes_accept_valid_payloads(monkeypatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "release-decision-secret")
    client = TestClient(app)
    headers = {"Authorization": "Bearer release-decision-secret"}
    proposal, bundle, manifest, index, capsule = _release_capsule_chain()

    decision_response = client.post(
        "/research/semantic-adjudication-bundle/release-decision-record",
        json={
            "capsule": capsule.model_dump(mode="json"),
            "decision": "BLOCK_ADJUDICATION",
            "decided_by": "api-test",
            "decision_reason": "route integration smoke",
            "index": index.model_dump(mode="json"),
            "bundle": bundle.model_dump(mode="json"),
            "manifest": manifest.model_dump(mode="json"),
            "proposal": proposal.model_dump(mode="json"),
            "require_manifest": True,
        },
        headers=headers,
    )
    assert decision_response.status_code == 200
    decision_record = decision_response.json()
    assert decision_record["schema_version"] == "semantic_adjudication_release_decision_record/v1"
    assert decision_record["experiment_id"] == proposal.experiment_id

    ledger_response = client.post(
        "/research/semantic-adjudication-bundle/release-decision-ledger",
        json={"decision_records": [decision_record]},
        headers=headers,
    )
    assert ledger_response.status_code == 200
    decision_ledger = ledger_response.json()
    assert decision_ledger["schema_version"] == "semantic_adjudication_release_decision_ledger/v1"
    assert decision_ledger["entry_count"] == 1

    certificate_response = client.post(
        "/research/semantic-adjudication-bundle/release-handoff-certificate",
        json={
            "decision_ledger": decision_ledger,
            "decision_records": [decision_record],
            "issued_by": "api-test",
            "issue_reason": "route integration smoke",
        },
        headers=headers,
    )
    assert certificate_response.status_code == 200
    certificate = certificate_response.json()
    assert certificate["schema_version"] == "semantic_adjudication_release_handoff_certificate/v1"
    assert certificate["experiment_id"] == proposal.experiment_id
