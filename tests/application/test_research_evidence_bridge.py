from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone

from strategy_validator.application.research_evidence_bridge import (
    attach_semantic_materialization_evidence,
    build_semantic_materialization_evidence,
)
from strategy_validator.application.research_feature_materialization import materialize_semantic_feature_for_proposal
from strategy_validator.contracts.semantic import FeatureFactoryArtifact
from strategy_validator.core.enums import EvidenceType
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _materialization():
    proposal = build_strategy_proposal(
        experiment_id="EXP-EVIDENCE-BRIDGE-001",
        strategy_name="SemanticBridgeAlpha",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
    )
    artifact = FeatureFactoryArtifact(
        event_id="event-bridge-001",
        forensic_status="adjudicated",
        novelty_score=0.7,
        polarity_score=0.1,
        belief_conflict=0.2,
        evidence_density=0.95,
    )
    return proposal, materialize_semantic_feature_for_proposal(
        proposal,
        artifact,
        published_at="2026-04-28T11:45:00Z",
        available_at="2026-04-28T11:50:00Z",
    )


def test_semantic_materialization_builds_checksummed_adjudication_evidence() -> None:
    _, materialization = _materialization()

    evidence = build_semantic_materialization_evidence(
        materialization,
        timestamp=datetime(2026, 4, 28, 12, 1, tzinfo=timezone.utc),
    )

    assert evidence.experiment_id == "EXP-EVIDENCE-BRIDGE-001"
    assert evidence.evidence_type is EvidenceType.TRIBUNAL_OPINION
    assert evidence.payload["schema_version"] == "semantic_research_materialization_evidence/v1"
    assert evidence.payload["pit_provenance"]["dataset_id"] == "semantic_tribunal_features/v1"
    assert evidence.payload["adjudication_use"]["semantic_signal_available"] is True

    canonical = json.dumps(evidence.payload, sort_keys=True, separators=(",", ":"), allow_nan=True)
    assert evidence.checksum == hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def test_semantic_materialization_evidence_attaches_to_matching_proposal() -> None:
    proposal, materialization = _materialization()

    evidence = attach_semantic_materialization_evidence(proposal, materialization)

    assert proposal.evidence_bundle.evidence_items == [evidence]
    assert evidence.evidence_id.endswith(":event-bridge-001")
