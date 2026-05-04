from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_integrity import (
    build_semantic_research_adjudication_gate_result,
    build_semantic_research_adjudication_gate_summary,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.evidence import SemanticArtifact, SpanCitation
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    return build_strategy_proposal(
        experiment_id="EXP-GATE-SUMMARY-001",
        strategy_name="GateSummaryAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )


def _artifact():
    return FeatureFactoryArtifact(
        event_id="event-gate-summary-001",
        forensic_status="adjudicated",
        novelty_score=0.63,
        polarity_score=0.04,
        belief_conflict=0.16,
        evidence_density=0.92,
    )


def _semantic_artifact():
    return SemanticArtifact(
        artifact_id="sem-gate-summary-001",
        model_name="deterministic-fixture",
        interpretation="semantic lane needs materialized PIT evidence",
        confidence=0.84,
        trust_state="REVIEWED",
        span_citations=[
            SpanCitation(source_id="fixture", start_char=0, end_char=8, source_checksum="12345678")
        ],
    )


def test_adjudication_gate_summary_passes_through_non_semantic_proposal() -> None:
    summary = build_semantic_research_adjudication_gate_summary(_proposal())

    assert summary.schema_version == "semantic_research_adjudication_gate_summary/v1"
    assert summary.gate_passed is True
    assert summary.gate_reason == "NO_SEMANTIC_RESEARCH_LANE"
    assert summary.recommended_action == "ALLOW_NON_SEMANTIC_ADJUDICATION"


def test_adjudication_gate_summary_blocks_semantic_lane_without_materialization() -> None:
    proposal = _proposal()
    proposal.evidence_bundle.semantic_artifacts.append(_semantic_artifact())

    summary = build_semantic_research_adjudication_gate_summary(proposal)

    assert summary.gate_passed is False
    assert summary.recommended_action == "QUARANTINE_BEFORE_ADJUDICATION"
    assert "SEMANTIC_RESEARCH_EVIDENCE_MISSING" in summary.blocker_codes


def test_adjudication_gate_summary_accepts_verified_materialization_and_gate_result_matches() -> None:
    proposal = _proposal()
    proposal.evidence_bundle.semantic_artifacts.append(_semantic_artifact())
    run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )

    summary = build_semantic_research_adjudication_gate_summary(proposal)
    gate = build_semantic_research_adjudication_gate_result(proposal)

    assert summary.gate_passed is True
    assert summary.recommended_action == "ALLOW_ADJUDICATION"
    assert summary.semantic_evidence_count == 1
    assert summary.data_spine_seal_present is True
    assert gate.gate_name == "SemanticResearchIntegrity"
    assert gate.passed is True
    assert gate.metric_value == 1.0
