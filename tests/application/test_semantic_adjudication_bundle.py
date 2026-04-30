from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_handoff_artifact,
    build_semantic_research_gate_artifact,
    verify_semantic_adjudication_bundle,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_bundle_is_sealed_and_verifiable() -> None:
    proposal = _verified_proposal()
    gate_artifact = build_semantic_research_gate_artifact(proposal)
    handoff_artifact = build_semantic_adjudication_handoff_artifact(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=True,
    )

    bundle = build_semantic_adjudication_bundle(
        proposal,
        gate_artifact=gate_artifact,
        handoff_artifact=handoff_artifact,
        require_gate_artifact=True,
    )
    report = verify_semantic_adjudication_bundle(bundle, proposal=proposal)

    assert bundle.schema_version == "semantic_adjudication_bundle/v1"
    assert bundle.gate_artifact == gate_artifact
    assert bundle.handoff_artifact == handoff_artifact
    assert report.verified is True
    assert report.recommended_action == "ACCEPT_SEMANTIC_ADJUDICATION_BUNDLE"


def test_semantic_adjudication_bundle_detects_checksum_drift() -> None:
    proposal = _verified_proposal()
    bundle = build_semantic_adjudication_bundle(proposal)
    tampered = bundle.model_copy(update={"proposal_digest": "0" * 64})

    report = verify_semantic_adjudication_bundle(tampered, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_BUNDLE_CHECKSUM_MISMATCH" in report.issue_codes
    assert "SEMANTIC_BUNDLE_PROPOSAL_DIGEST_MISMATCH" in report.issue_codes


def test_semantic_adjudication_bundle_detects_proposal_drift() -> None:
    proposal = _verified_proposal()
    bundle = build_semantic_adjudication_bundle(proposal)
    proposal.strategy_name = "DriftedStrategyName"

    report = verify_semantic_adjudication_bundle(bundle, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_BUNDLE_PROPOSAL_DIGEST_MISMATCH" in report.issue_codes
