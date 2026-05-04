from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_release_capsule,
    build_semantic_adjudication_release_decision_record,
)
from strategy_validator.proposers.experiments.generator import build_strategy_proposal


def _ready_release_decision_record():
    proposal = build_strategy_proposal(
        experiment_id="EXP-SEMANTIC-HANDOFF-001",
        strategy_name="HandoffSmoke",
        proposer_id="ci-test",
        evaluation_time_utc=datetime(2026, 4, 28, 12, 0, tzinfo=timezone.utc),
        market_data_subject_id="AAPL",
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
    )
    bundle = build_semantic_adjudication_bundle(proposal, require_gate_artifact=False)
    manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
    index = build_semantic_adjudication_bundle_release_index(bundle, manifest=manifest, proposal=proposal)
    capsule = build_semantic_adjudication_release_capsule(
        index, bundle=bundle, manifest=manifest, proposal=proposal
    )
    return build_semantic_adjudication_release_decision_record(
        capsule,
        decision="ACCEPT_FOR_ADJUDICATION",
        decided_by="ci-test",
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=True,
    )


def test_release_decision_record_contracts_and_builders_are_declared() -> None:
    contracts = Path("strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    integrity = Path("strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticAdjudicationReleaseDecisionRecord" in contracts
    assert "class SemanticAdjudicationReleaseDecisionRecordVerificationReport" in contracts
    assert "class SemanticAdjudicationReleaseDecisionRecordSummary" in contracts
    assert "semantic_adjudication_release_decision_record/v1" in contracts
    assert "def build_semantic_adjudication_release_decision_record" in integrity
    assert "def verify_semantic_adjudication_release_decision_record" in integrity
    assert "def summarize_semantic_adjudication_release_decision_record" in integrity
    assert "HAND_OFF_TO_VALIDATOR_ADJUDICATION" in integrity
    assert "SEMANTIC_RELEASE_DECISION_ACCEPTED_UNREADY_CAPSULE" in integrity
    assert "SEMANTIC_RELEASE_DECISION_RECORD_CHECKSUM_MISMATCH" in integrity


def test_release_decision_record_is_exported_from_application_facade() -> None:
    exports = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")
    root = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")

    assert "build_semantic_adjudication_release_decision_record" in exports
    assert "verify_semantic_adjudication_release_decision_record" in exports
    assert "summarize_semantic_adjudication_release_decision_record" in exports
    assert "build_semantic_adjudication_release_decision_record" in root
    assert "verify_semantic_adjudication_release_decision_record" in root
    assert "summarize_semantic_adjudication_release_decision_record" in root
