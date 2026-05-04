from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_readiness_report,
    build_semantic_research_gate_artifact,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_readiness_accepts_verified_gate_artifact() -> None:
    proposal = _verified_proposal()
    artifact = build_semantic_research_gate_artifact(proposal)

    report = build_semantic_adjudication_readiness_report(
        proposal,
        gate_artifact=artifact,
        require_gate_artifact=True,
    )

    assert report.schema_version == "semantic_adjudication_readiness/v1"
    assert report.ready_for_adjudication is True
    assert report.gate_passed is True
    assert report.gate_artifact_required is True
    assert report.gate_artifact_present is True
    assert report.gate_artifact_verified is True
    assert report.gate_artifact_id == artifact.artifact_id
    assert report.recommended_action == "HAND_TO_ADJUDICATOR"


def test_semantic_adjudication_readiness_blocks_missing_required_artifact() -> None:
    proposal = _verified_proposal()

    report = build_semantic_adjudication_readiness_report(proposal, require_gate_artifact=True)

    assert report.ready_for_adjudication is False
    assert "SEMANTIC_GATE_ARTIFACT_REQUIRED" in report.blocker_codes
    assert report.recommended_action == "BLOCK_ADJUDICATION_HANDOFF"


def test_semantic_adjudication_readiness_blocks_artifact_drift() -> None:
    proposal = _verified_proposal()
    artifact = build_semantic_research_gate_artifact(proposal)
    tampered = artifact.model_copy(update={"proposal_digest": "0" * 64})

    report = build_semantic_adjudication_readiness_report(proposal, gate_artifact=tampered)

    assert report.ready_for_adjudication is False
    assert "SEMANTIC_GATE_ARTIFACT_CHECKSUM_MISMATCH" in report.blocker_codes
    assert "SEMANTIC_GATE_ARTIFACT_PROPOSAL_DIGEST_MISMATCH" in report.blocker_codes
