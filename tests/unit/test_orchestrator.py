from datetime import datetime, timezone
from typing import List, Optional

import pytest

from strategy_validator.contracts.evidence import (
    Evidence,
    EvidenceBundle,
    ReproducibilityManifest,
    SemanticArtifact,
    SpanCitation,
)
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.core.exceptions import AdjudicationError
from strategy_validator.ledger import reader as ledger_reader
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
    return EvidenceBundle(reproducibility=_repro(), benchmark_rung="L1", search_breadth=5)


def _passing_bundle() -> EvidenceBundle:
    b = _bundle()
    b.dsr_estimate = 0.5
    b.pbo_estimate = 0.1
    b.cpcv_passed = True
    b.cpcv_folds = 5
    b.cpcv_path_coverage = 1.0
    b.cpcv_path_stability = 0.1
    b.decoy_survival_passed = True
    b.decoy_suite_version = "decoy-v1"
    b.decoy_coverage = 1.0
    b.incrementality_significant = True
    b.incrementality_p_value = 0.001
    
    # Baseline semantic artifact with spans
    b.semantic_artifacts.append(
        SemanticArtifact(
            artifact_id="sa_baseline",
            model_name="llm-v1",
            interpretation="Valid Alpha Claim",
            confidence=0.9,
            span_citations=[SpanCitation(source_id="s1", start_char=0, end_char=10, source_checksum="0"*8)]
        )
    )
    return b


def _ev(experiment_id: str = "EXP-1", **payload) -> Evidence:
    # Baseline passing evidence defaults
    defaults = {
        "pit_integrity_ok": True,
        "benchmark_passed": True,
        "benchmark_delta": 0.02,
        "benchmark_id": "SPY",
        "benchmark_version": "bench-v1",
    }
    # Sentinel-based override: None means DELETE key, otherwise update
    for k, v in payload.items():
        if v is None:
            if k in defaults:
                del defaults[k]
        else:
            defaults[k] = v

    return Evidence(
        evidence_id="e1",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.COST_SUMMARY,
        timestamp=datetime.now(timezone.utc),
        payload=defaults,
        source_module="tests",
        checksum="0" * 64,
    )


def test_adjudicate_promotable_when_gates_pass() -> None:
    bundle = _passing_bundle()
    exp = ExperimentManifest(
        experiment_id="EXP-1",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-1",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.01,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    assert state == PromotionState.PROMOTABLE
    loaded = ledger_reader.get_experiment("EXP-1")
    assert loaded is not None
    assert loaded.state == PromotionState.PROMOTABLE


def test_adjudicate_rejects_midpoint_economics() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-MID",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-MID",
                midpoint_only=True,
            )
        ],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_rejects_on_pit_failure() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-PIT-FAIL",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    state = adjudicate(exp, [_ev("EXP-PIT-FAIL", pit_integrity_ok=False)])
    assert state == PromotionState.REJECTED


def test_adjudicate_invalid_on_future_leakage() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-3",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    state = adjudicate(exp, [_ev("EXP-3", future_leakage_detected=True)])
    assert state == PromotionState.INVALID


def test_adjudicate_quarantines_semantic_without_spans() -> None:
    bundle = _passing_bundle()
    # Clear spans to trigger quarantine
    bundle.semantic_artifacts[0].span_citations = []
    
    exp = ExperimentManifest(
        experiment_id="EXP-SEM",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp, 
        [_ev("EXP-SEM")]
    )
    assert state == PromotionState.QUARANTINED


def test_adjudicate_conditional_without_dsr_pbo() -> None:
    bundle = _passing_bundle()
    bundle.dsr_estimate = None
    bundle.pbo_estimate = None
    
    exp = ExperimentManifest(
        experiment_id="EXP-CON",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-CON")],
    )
    assert state == PromotionState.CONDITIONAL


def test_adjudicate_canary_on_regime_instability() -> None:
    bundle = _passing_bundle()
    bundle.cpcv_path_stability = 2.0  # Above threshold
    
    exp = ExperimentManifest(
        experiment_id="EXP-STAB",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-STAB", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.QUARANTINED


def test_adjudicate_invalid_when_benchmark_rung_unknown() -> None:
    bundle = _passing_bundle()
    bundle.benchmark_rung = "unknown-rung"
    exp = ExperimentManifest(
        experiment_id="EXP-BAD-RUNG",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(exp, [_ev("EXP-BAD-RUNG", pit_integrity_ok=True, benchmark_passed=True)])
    assert state == PromotionState.INVALID


def test_adjudicate_invalid_when_benchmark_id_mismatches_rung() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-BID-MISMATCH",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-BID-MISMATCH",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.02,
                benchmark_id="QQQ", # Rung L1 expects SPY
                benchmark_version="bench-v1",
            )
        ],
    )
    assert state == PromotionState.INVALID


def test_adjudicate_materializes_dsr_pbo_from_evidence() -> None:
    # Bundle is empty of metrics
    bundle = _bundle()
    exp = ExperimentManifest(
        experiment_id="EXP-MTP",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-MTP",
                observed_sharpe=0.3,
                sample_size=100,
                cpcv_passed=True,
                cpcv_path_coverage=0.9,
                cpcv_path_stability=0.1,
                incrementality_significant=True,
                incrementality_p_value=0.001,
                decoy_survival_passed=True,
                decoy_coverage=1.0,
            )
        ],
    )
    assert exp.evidence_bundle.dsr_estimate is not None
    # INVALID because of missing folds while asserting pass
    assert state == PromotionState.INVALID


def test_adjudicate_rejects_when_benchmark_delta_below_rung_minimum() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-LOW-DELTA",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-LOW-DELTA",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.001,  # Rung L1 requires 0.01
                benchmark_id="SPY",
                benchmark_version="bench-v1",
            )
        ],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_rejects_when_cpcv_hook_fails() -> None:
    bundle = _passing_bundle()
    bundle.cpcv_passed = False
    exp = ExperimentManifest(
        experiment_id="EXP-CPCV-FAIL",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-CPCV-FAIL", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_rejects_when_decoy_hook_fails() -> None:
    bundle = _passing_bundle()
    bundle.decoy_survival_passed = False
    exp = ExperimentManifest(
        experiment_id="EXP-DECOY-FAIL",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-DECOY-FAIL", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_invalid_when_cpcv_missing_folds() -> None:
    bundle = _passing_bundle()
    bundle.cpcv_folds = None
    exp = ExperimentManifest(
        experiment_id="EXP-CPCV-META",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [
            _ev(
                "EXP-CPCV-META",
                pit_integrity_ok=True,
                benchmark_passed=True,
                benchmark_delta=0.02,
                benchmark_id="SPY",
                benchmark_version="bench-v1",
                cpcv_passed=True,
                cpcv_folds=None # Explicitly missing
            )
        ],
    )
    assert state == PromotionState.INVALID


def test_adjudicate_rejects_untyped_partial_benchmark_payload() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-PARTIAL-BENCH",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_passing_bundle(),
    )
    # Explicitly missing benchmark_delta via sentinel
    state = adjudicate(
        exp,
        [_ev("EXP-PARTIAL-BENCH", benchmark_delta=None)],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_rejects_when_cpcv_coverage_below_threshold() -> None:
    bundle = _passing_bundle()
    bundle.cpcv_path_coverage = 0.6  # Below 0.7
    exp = ExperimentManifest(
        experiment_id="EXP-CPCV-THR",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-CPCV-THR", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.REJECTED


def test_adjudicate_rejects_when_decoy_coverage_below_threshold() -> None:
    bundle = _passing_bundle()
    bundle.decoy_coverage = 0.75  # Below 0.8
    exp = ExperimentManifest(
        experiment_id="EXP-DECOY-THR",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=bundle,
    )
    state = adjudicate(
        exp,
        [_ev("EXP-DECOY-THR", pit_integrity_ok=True, benchmark_passed=True, benchmark_delta=0.02, benchmark_id="SPY", benchmark_version="bench-v1")],
    )
    assert state == PromotionState.REJECTED


def test_evidence_experiment_mismatch_raises() -> None:
    exp = ExperimentManifest(
        experiment_id="EXP-4",
        strategy_name="s",
        version="1",
        proposer_id="p",
        evidence_bundle=_bundle(),
    )
    bad = Evidence(
        evidence_id="x",
        experiment_id="OTHER",
        evidence_type=EvidenceType.COST_SUMMARY,
        payload={},
        source_module="tests",
        checksum="0" * 64,
    )
    with pytest.raises(AdjudicationError, match="mismatch"):
        adjudicate(exp, [bad])
