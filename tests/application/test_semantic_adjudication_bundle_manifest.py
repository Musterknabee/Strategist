from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
    summarize_semantic_adjudication_bundle,
    verify_semantic_adjudication_bundle_manifest,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_bundle_summary_is_operator_ready() -> None:
    proposal = _verified_proposal()
    bundle = build_semantic_adjudication_bundle(proposal)

    summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)

    assert summary.schema_version == "semantic_adjudication_bundle_summary/v1"
    assert summary.verified is True
    assert summary.ready_for_adjudication is True
    assert summary.recommended_action == "HAND_TO_ADJUDICATOR"
    assert summary.gate_artifact_present is True
    assert summary.semantic_evidence_count == 1


def test_semantic_adjudication_bundle_manifest_is_sealed_and_verifiable() -> None:
    proposal = _verified_proposal()
    bundle = build_semantic_adjudication_bundle(proposal)

    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    report = verify_semantic_adjudication_bundle_manifest(manifest, bundle=bundle, proposal=proposal)

    assert manifest.schema_version == "semantic_adjudication_bundle_manifest/v1"
    assert manifest.bundle_payload_checksum == bundle.payload_checksum
    assert manifest.summary.ready_for_adjudication is True
    assert report.verified is True
    assert report.recommended_action == "ACCEPT_SEMANTIC_ADJUDICATION_BUNDLE_MANIFEST"


def test_semantic_adjudication_bundle_manifest_detects_bundle_drift() -> None:
    proposal = _verified_proposal()
    bundle = build_semantic_adjudication_bundle(proposal)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    tampered = manifest.model_copy(update={"bundle_payload_checksum": "0" * 64})

    report = verify_semantic_adjudication_bundle_manifest(tampered, bundle=bundle, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_BUNDLE_MANIFEST_CHECKSUM_MISMATCH" in report.issue_codes
    assert "SEMANTIC_BUNDLE_MANIFEST_BUNDLE_CHECKSUM_MISMATCH" in report.issue_codes
