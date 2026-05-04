from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_integrity import verify_proposal_semantic_research_integrity
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    return build_strategy_proposal(
        experiment_id="EXP-SEMANTIC-INTEGRITY-001",
        strategy_name="SemanticIntegrityAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )


def _artifact():
    return FeatureFactoryArtifact(
        event_id="event-semantic-integrity-001",
        forensic_status="adjudicated",
        novelty_score=0.61,
        polarity_score=0.09,
        belief_conflict=0.17,
        evidence_density=0.91,
    )


def test_proposal_semantic_research_integrity_accepts_preflight_attached_evidence() -> None:
    proposal = _proposal()
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )

    report = verify_proposal_semantic_research_integrity(proposal)

    assert report.schema_version == "semantic_research_integrity/v1"
    assert report.verified is True
    assert report.semantic_evidence_count == 1
    assert report.data_spine_seal_present is True
    assert report.recommended_action == "READY_FOR_ADJUDICATION_PREFLIGHT"
    assert report.issue_codes == []


def test_proposal_semantic_research_integrity_blocks_missing_evidence() -> None:
    report = verify_proposal_semantic_research_integrity(_proposal())

    assert report.verified is False
    assert report.semantic_evidence_count == 0
    assert "SEMANTIC_RESEARCH_EVIDENCE_MISSING" in report.issue_codes


def test_proposal_semantic_research_integrity_blocks_missing_data_spine_seal() -> None:
    proposal = _proposal()
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )
    proposal.evidence_bundle.data_spine_seal = None

    report = verify_proposal_semantic_research_integrity(proposal)

    assert report.verified is False
    assert "SEMANTIC_RESEARCH_DATA_SPINE_SEAL_MISSING" in report.issue_codes
    assert "SEMANTIC_RESEARCH_DATA_SPINE_SEAL_MISMATCH" in report.issue_codes


def test_proposal_semantic_research_integrity_blocks_checksum_drift() -> None:
    proposal = _proposal()
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )
    proposal.evidence_bundle.evidence_items[0].payload["adjudication_use"]["semantic_signal_available"] = False

    report = verify_proposal_semantic_research_integrity(proposal)

    assert report.verified is False
    assert "SEMANTIC_EVIDENCE_CHECKSUM_MISMATCH" in report.issue_codes
