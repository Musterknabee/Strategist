from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_integrity import (
    summarize_semantic_research_integrity_report,
    verify_proposal_semantic_research_integrity,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    return build_strategy_proposal(
        experiment_id="EXP-SEMANTIC-SUMMARY-001",
        strategy_name="SemanticSummaryAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )


def _artifact():
    return FeatureFactoryArtifact(
        event_id="event-semantic-summary-001",
        forensic_status="adjudicated",
        novelty_score=0.61,
        polarity_score=0.09,
        belief_conflict=0.17,
        evidence_density=0.91,
    )


def test_semantic_integrity_summary_is_compact_and_operator_stable() -> None:
    proposal = _proposal()
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )
    report = verify_proposal_semantic_research_integrity(proposal)

    summary = summarize_semantic_research_integrity_report(report)

    assert summary["schema_version"] == "semantic_research_integrity_summary/v1"
    assert summary["verified"] is True
    assert summary["recommended_action"] == "READY_FOR_ADJUDICATION_PREFLIGHT"
    assert summary["semantic_evidence_count"] == 1
    assert summary["blocker_codes"] == []


def test_semantic_integrity_summary_surfaces_blocker_codes() -> None:
    report = verify_proposal_semantic_research_integrity(_proposal())

    summary = summarize_semantic_research_integrity_report(report)

    assert summary["verified"] is False
    assert "SEMANTIC_RESEARCH_EVIDENCE_MISSING" in summary["blocker_codes"]
