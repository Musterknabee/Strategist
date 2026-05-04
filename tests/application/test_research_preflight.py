from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal():
    return build_strategy_proposal(
        experiment_id="EXP-RESEARCH-PREFLIGHT-001",
        strategy_name="SemanticPreflightAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )


def _artifact():
    return FeatureFactoryArtifact(
        event_id="event-preflight-001",
        forensic_status="adjudicated",
        novelty_score=0.77,
        polarity_score=0.12,
        belief_conflict=0.22,
        evidence_density=0.88,
    )


def test_semantic_research_preflight_attaches_verified_evidence_and_seal() -> None:
    proposal = _proposal()

    report = run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )

    assert report.schema_version == "semantic_research_preflight/v1"
    assert report.evidence_verified is True
    assert report.recommended_action == "ATTACH_TO_ADJUDICATION_EVIDENCE"
    assert report.attached_evidence_count == 1
    assert report.data_spine_fingerprint
    assert proposal.evidence_bundle.evidence_items[0].evidence_id == report.evidence_id
    assert proposal.evidence_bundle.data_spine_seal is not None


def test_semantic_research_preflight_dry_run_does_not_mutate_proposal() -> None:
    proposal = _proposal()

    report = run_semantic_research_preflight(
        proposal,
        _artifact(),
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
        attach_to_proposal=False,
    )

    assert report.evidence_verified is True
    assert report.attached_evidence_count == 0
    assert report.data_spine_fingerprint is None
    assert proposal.evidence_bundle.evidence_items == []
    assert proposal.evidence_bundle.data_spine_seal is None
