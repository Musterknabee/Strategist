from datetime import datetime, timezone

import pytest

from strategy_validator.contracts.evidence import (
    Evidence,
    EvidenceBundle,
    ReproducibilityManifest,
    SemanticArtifact,
)
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.data_spine.joins.as_of import AsOfJoinEngine
from strategy_validator.validator.orchestrator import adjudicate


def _repro() -> ReproducibilityManifest:
    return ReproducibilityManifest(
        code_hash="a" * 64,
        data_snapshot_hash="b" * 64,
        universe_hash="c" * 64,
        feature_graph_hash="d" * 64,
        parameter_manifest_hash="e" * 64,
        benchmark_version="bench-v1",
        cost_model_version="cost-v1",
        calendar_version="cal-v1",
    )


def _bundle() -> EvidenceBundle:
    return EvidenceBundle(reproducibility=_repro(), benchmark_rung="L1", search_breadth=1)


def _ev(experiment_id: str, **payload) -> Evidence:
    return Evidence(
        evidence_id=f"ev-{experiment_id}-{len(payload)}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="tests",
        checksum="f" * 64,
    )


def test_pit_join_rejects_future_available_rows() -> None:
    import pandas as pd

    decisions = pd.DataFrame(
        {"symbol": ["A"], "decision_at": [pd.Timestamp("2024-01-01T10:00:00Z")]}
    )
    features = pd.DataFrame(
        {
            "symbol": ["A", "A"],
            "available_at": [
                pd.Timestamp("2024-01-01T10:01:00Z"),
                pd.Timestamp("2024-01-01T09:59:00Z"),
            ],
            "value": [999.0, 1.0],
        }
    )
    engine = AsOfJoinEngine(
        decision_time_col="decision_at",
        available_at_col="available_at",
        group_keys=["symbol"],
    )
    out_df, provenance = engine.execute(decisions, features)
    assert len(out_df) == 1
    assert float(out_df.loc[0, "value"]) == 1.0


def test_missing_reproducibility_hashes_are_rejected_by_contract() -> None:
    with pytest.raises(Exception):
        ReproducibilityManifest(
            code_hash="",
            data_snapshot_hash="",
            universe_hash="",
            feature_graph_hash="",
            parameter_manifest_hash="",
            benchmark_version="",
            cost_model_version="",
            calendar_version="",
        )


def test_midpoint_only_promotion_attempt_is_rejected() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-MID",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    state = adjudicate(exp, [_ev("EXP-MID", economics_model="midpoint_only", benchmark_passed=True)])
    assert state == PromotionState.REJECTED


def test_semantic_artifact_without_span_references_is_quarantined() -> None:
    bundle = _bundle()
    bundle.semantic_artifacts.append(
        SemanticArtifact(
            artifact_id="a1",
            model_name="llm-x",
            interpretation="narrative only",
            confidence=0.7,
            span_citations=[],
        )
    )
    bundle.decoy_survival_passed = True
    bundle.decoy_coverage = 1.0
    exp = ExperimentManifest(
        experiment_id="EXP-SEMANTIC",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    exp.evidence_bundle = bundle
    eid = "EXP-SEMANTIC"
    payload = {
        "cpcv_passed": True, "cpcv_folds": 5, "cpcv_path_coverage": 1.0, "cpcv_path_stability": 0.1,
        "incrementality_p_value": 0.01, "incrementality_significant": True,
        "dsr_estimate": 0.5, "pbo_estimate": 0.1,
        "decoy_survival_passed": True, "decoy_coverage": 1.0,
        "benchmark_passed": True, "benchmark_delta": 0.1, "benchmark_id": "SPY", "benchmark_version": "bench-v1"
    }
    exp.evidence_bundle.decoy_survival_passed = True
    exp.evidence_bundle.decoy_coverage = 1.0
    exp.evidence_bundle.dsr_estimate = 0.5
    exp.evidence_bundle.pbo_estimate = 0.1
    exp.evidence_bundle.cpcv_passed = True
    exp.evidence_bundle.cpcv_folds = 5
    exp.evidence_bundle.cpcv_path_coverage = 1.0
    exp.evidence_bundle.search_breadth = 3
    
    state = adjudicate(exp, [_ev(eid, **payload)])
    assert state == PromotionState.QUARANTINED


def test_benchmark_delta_below_rung_minimum_fails() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-BENCH-DELTA",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    state = adjudicate(
        exp,
        [_ev("EXP-BENCH-DELTA", benchmark_passed=True, benchmark_delta=0.001, pit_integrity_ok=True)],
    )
    assert state == PromotionState.REJECTED


def test_cpcv_hook_failure_blocks_promotion() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-CPCV-HOOK",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    state = adjudicate(
        exp,
        [_ev("EXP-CPCV-HOOK", benchmark_passed=True, benchmark_delta=0.02, pit_integrity_ok=True, cpcv_passed=False)],
    )
    assert state == PromotionState.REJECTED


def test_decoy_hook_failure_blocks_promotion() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-DECOY-HOOK",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-DECOY-HOOK",
                benchmark_passed=True,
                benchmark_delta=0.02,
                pit_integrity_ok=True,
                decoy_survival_passed=False,
            )
        ],
    )
    assert state == PromotionState.REJECTED


def test_missing_benchmark_delta_forces_non_promotable_state() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-NO-DELTA",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    state = adjudicate(exp, [_ev("EXP-NO-DELTA", benchmark_passed=True, pit_integrity_ok=True)])
    assert state in {PromotionState.REJECTED, PromotionState.CONDITIONAL, PromotionState.INVALID}
    assert state != PromotionState.PROMOTABLE
