from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_handoff_artifact,
    build_semantic_research_gate_artifact,
    verify_semantic_adjudication_handoff_artifact,
)
from tests.application.test_research_gate_artifact import _verified_proposal


def test_semantic_adjudication_handoff_artifact_is_sealed_and_verifiable() -> None:
    proposal = _verified_proposal()
    gate_artifact = build_semantic_research_gate_artifact(proposal)

    handoff = build_semantic_adjudication_handoff_artifact(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=True,
    )
    report = verify_semantic_adjudication_handoff_artifact(handoff, proposal=proposal)

    assert handoff.schema_version == "semantic_adjudication_handoff_artifact/v1"
    assert handoff.readiness_report.ready_for_adjudication is True
    assert handoff.gate_artifact == gate_artifact
    assert report.verified is True
    assert report.recommended_action == "ACCEPT_SEMANTIC_ADJUDICATION_HANDOFF"


def test_semantic_adjudication_handoff_artifact_detects_proposal_drift() -> None:
    proposal = _verified_proposal()
    gate_artifact = build_semantic_research_gate_artifact(proposal)
    handoff = build_semantic_adjudication_handoff_artifact(proposal, gate_artifact=gate_artifact)
    proposal.strategy_name = "DriftedStrategyName"

    report = verify_semantic_adjudication_handoff_artifact(handoff, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_HANDOFF_PROPOSAL_DIGEST_MISMATCH" in report.issue_codes
    assert "SEMANTIC_HANDOFF_READINESS_DRIFT" in report.issue_codes


def test_semantic_adjudication_handoff_artifact_detects_checksum_drift() -> None:
    proposal = _verified_proposal()
    handoff = build_semantic_adjudication_handoff_artifact(proposal)
    tampered = handoff.model_copy(update={"proposal_digest": "0" * 64})

    report = verify_semantic_adjudication_handoff_artifact(tampered, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_HANDOFF_ARTIFACT_CHECKSUM_MISMATCH" in report.issue_codes
    assert "SEMANTIC_HANDOFF_PROPOSAL_DIGEST_MISMATCH" in report.issue_codes
