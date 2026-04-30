from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_integrity import (
    build_semantic_research_gate_artifact,
    verify_semantic_research_gate_artifact,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.evidence import SemanticArtifact, SpanCitation
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    proposal = build_strategy_proposal(
        experiment_id="EXP-GATE-ARTIFACT-001",
        strategy_name="GateArtifactAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )
    proposal.evidence_bundle.semantic_artifacts.append(
        SemanticArtifact(
            artifact_id="sem-gate-artifact-001",
            model_name="deterministic-fixture",
            interpretation="semantic lane requires sealed gate artifact",
            confidence=0.82,
            trust_state="REVIEWED",
            span_citations=[SpanCitation(source_id="fixture", start_char=0, end_char=8, source_checksum="12345678")],
        )
    )
    return proposal


def _artifact():
    return FeatureFactoryArtifact(
        event_id="event-gate-artifact-001",
        forensic_status="adjudicated",
        novelty_score=0.61,
        polarity_score=0.02,
        belief_conflict=0.11,
        evidence_density=0.88,
    )


def _verified_proposal():
    proposal = _proposal()
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )
    return proposal


def test_semantic_gate_artifact_is_checksummed_and_verifiable() -> None:
    proposal = _verified_proposal()

    artifact = build_semantic_research_gate_artifact(proposal)
    report = verify_semantic_research_gate_artifact(artifact, proposal=proposal)

    assert artifact.schema_version == "semantic_research_gate_artifact/v1"
    assert artifact.summary.gate_passed is True
    assert artifact.semantic_evidence_checksums == [proposal.evidence_bundle.evidence_items[0].checksum]
    assert artifact.data_spine_fingerprint == proposal.evidence_bundle.data_spine_seal.fingerprint
    assert report.verified is True
    assert report.recommended_action == "ACCEPT_SEMANTIC_GATE_ARTIFACT"


def test_semantic_gate_artifact_detects_summary_drift() -> None:
    proposal = _verified_proposal()
    artifact = build_semantic_research_gate_artifact(proposal)
    tampered = artifact.model_copy(update={"summary": artifact.summary.model_copy(update={"gate_passed": False})})

    report = verify_semantic_research_gate_artifact(tampered, proposal=proposal)

    assert report.verified is False
    assert "SEMANTIC_GATE_ARTIFACT_CHECKSUM_MISMATCH" in report.issue_codes
    assert "SEMANTIC_GATE_ARTIFACT_SUMMARY_DRIFT" in report.issue_codes
