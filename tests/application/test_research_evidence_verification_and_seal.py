from __future__ import annotations

from datetime import datetime, timezone

from strategy_validator.application.research_evidence_bridge import (
    attach_semantic_materialization_data_spine_seal,
    attach_semantic_materialization_evidence,
    build_semantic_materialization_data_spine_seal,
    build_semantic_materialization_evidence,
    verify_semantic_materialization_evidence,
)
from strategy_validator.application.research_feature_materialization import materialize_semantic_feature_for_proposal
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _proposal_and_materialization():
    proposal = build_strategy_proposal(
        experiment_id="EXP-SEMANTIC-VERIFY-001",
        strategy_name="SemanticVerificationAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )
    artifact = FeatureFactoryArtifact(
        event_id="event-semantic-verify-001",
        forensic_status="adjudicated",
        novelty_score=0.82,
        polarity_score=0.14,
        belief_conflict=0.11,
        evidence_density=0.91,
    )
    materialization = materialize_semantic_feature_for_proposal(
        proposal,
        artifact,
        published_at="2026-04-28T11:42:00Z",
        available_at="2026-04-28T11:47:00Z",
    )
    return proposal, materialization


def test_semantic_materialization_evidence_verifier_accepts_deterministic_bridge() -> None:
    proposal, materialization = _proposal_and_materialization()
    evidence = build_semantic_materialization_evidence(materialization)

    report = verify_semantic_materialization_evidence(
        evidence,
        materialization=materialization,
        proposal=proposal,
    )

    assert report.verified is True
    assert report.issue_count == 0
    assert report.checksum == report.expected_checksum
    assert report.schema_version == "semantic_research_materialization_evidence/v1"


def test_semantic_materialization_evidence_verifier_detects_checksum_drift() -> None:
    _, materialization = _proposal_and_materialization()
    evidence = build_semantic_materialization_evidence(materialization)
    tampered = evidence.model_copy(update={"payload": {**evidence.payload, "joined_row_count": 999}})

    report = verify_semantic_materialization_evidence(tampered, materialization=materialization)

    assert report.verified is False
    assert {issue.code for issue in report.issues} >= {"SEMANTIC_EVIDENCE_CHECKSUM_MISMATCH"}


def test_semantic_materialization_data_spine_seal_is_deterministic_and_deduped() -> None:
    proposal, materialization = _proposal_and_materialization()

    first = attach_semantic_materialization_data_spine_seal(proposal, materialization)
    second = attach_semantic_materialization_data_spine_seal(proposal, materialization)
    rebuilt = build_semantic_materialization_data_spine_seal(materialization)

    assert first.fingerprint == second.fingerprint == rebuilt.fingerprint
    assert len(second.as_of_provenance) == 1
    assert second.as_of_provenance[0].dataset_id == "semantic_tribunal_features/v1"
    assert proposal.evidence_bundle.data_spine_seal is second


def test_attach_semantic_materialization_evidence_also_attaches_data_spine_seal() -> None:
    proposal, materialization = _proposal_and_materialization()

    evidence = attach_semantic_materialization_evidence(proposal, materialization)

    assert proposal.evidence_bundle.evidence_items == [evidence]
    assert proposal.evidence_bundle.data_spine_seal is not None
    assert proposal.evidence_bundle.data_spine_seal.as_of_provenance[0].row_count_after == 1
