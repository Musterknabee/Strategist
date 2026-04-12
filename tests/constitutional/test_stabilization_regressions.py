import pytest
import pandas as pd
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.ledger import reader as ledger_reader

def _repro():
    return ReproducibilityManifest(
        code_hash="a"*64, data_snapshot_hash="b"*64, 
        universe_hash="c"*64, feature_graph_hash="d"*64,
        parameter_manifest_hash="e"*64, benchmark_version="bench-v1",
        cost_model_version="v1", calendar_version="v1"
    )

def _bundle():
    return EvidenceBundle(reproducibility=_repro(), benchmark_rung="L1", search_breadth=1)

def _ev(experiment_id, **payload):
    defaults = {
        "benchmark_id": "SPY", "benchmark_version": "bench-v1",
        "benchmark_passed": True, "benchmark_delta": 0.05,
        "pit_integrity_ok": True,
    }
    defaults.update(payload)
    return Evidence(
        evidence_id=f"ev-{experiment_id}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime(2026, 4, 12, tzinfo=timezone.utc),
        payload=defaults,
        source_module="tests",
        checksum="0"*64
    )

def test_asserted_cpcv_pass_without_metadata_is_invalid():
    """REGRESSION: cpcv_passed=True without folds/coverage must be INVALID."""
    exp = ExperimentManifest(
        experiment_id="REG-CPCV-INVALID",
        strategy_name="s", version="1", proposer_id="p",
        evidence_bundle=_bundle()
    )
    # Claim pass but omit metadata
    adjudicate(exp, [_ev(exp.experiment_id, cpcv_passed=True)])
    
    assert exp.state == PromotionState.INVALID
    decision = exp.promotion_history[-1]
    assert any("INVALID_CPCV_CLAIM" in g.note for g in decision.gate_results if g.gate_name == "RobustnessAudit")

def test_asserted_benchmark_pass_with_wrong_version_is_invalid():
    """REGRESSION: claimed benchmark success without valid rung context is INVALID."""
    exp = ExperimentManifest(
        experiment_id="REG-BENCH-INVALID",
        strategy_name="s", version="1", proposer_id="p",
        evidence_bundle=_bundle()
    )
    # Claim pass but use wrong version
    adjudicate(exp, [_ev(exp.experiment_id, benchmark_passed=True, benchmark_version="WRONG-V")])
    
    assert exp.state == PromotionState.INVALID
    decision = exp.promotion_history[-1]
    assert any(g.reason == "BENCHMARK_ID_MISMATCH" for g in decision.gate_results if g.gate_name == "BenchmarkContext")

def test_ledger_retraction_on_disqualification():
    """REGRESSION: list_promoted_strategies does not show strategies after they transition out of PROMOTABLE."""
    eid = f"REG-LEDGER-{datetime.now().timestamp()}"
    exp = ExperimentManifest(
        experiment_id=eid,
        strategy_name="s", version="1", proposer_id="p",
        evidence_bundle=_bundle()
    )
    
    # 1. Make it Promotable
    payload = {
        "cpcv_passed": True, "cpcv_folds": 5, "cpcv_path_coverage": 1.0, "cpcv_path_stability": 0.1,
        "incrementality_p_value": 0.01, "incrementality_significant": True,
        "dsr_estimate": 0.5, "pbo_estimate": 0.1,
        "decoy_survival_passed": True, "decoy_coverage": 1.0,
        "benchmark_passed": True, "benchmark_delta": 0.1, "benchmark_id": "SPY", "benchmark_version": "bench-v1"
    }
    # We must also set these in the bundle for the test to reach PROMOTABLE 
    # as some gates check the bundle directly.
    exp.evidence_bundle.decoy_survival_passed = True
    exp.evidence_bundle.decoy_coverage = 1.0
    exp.evidence_bundle.dsr_estimate = 0.5
    exp.evidence_bundle.pbo_estimate = 0.1
    exp.evidence_bundle.cpcv_passed = True
    exp.evidence_bundle.cpcv_folds = 5
    exp.evidence_bundle.cpcv_path_coverage = 1.0
    exp.evidence_bundle.decoy_suite_version = "decoy-v1"
    exp.evidence_bundle.cpcv_path_stability = 0.1
    
    adjudicate(exp, [_ev(eid, **payload)])
    assert exp.state == PromotionState.PROMOTABLE
    
    promoted = ledger_reader.list_promoted_strategies()
    assert any(m.experiment_id == eid for m in promoted)
    
    # 2. Disqualify it (transition to INVALID)
    adjudicate(exp, [_ev(eid, pit_integrity_ok=False)])
    assert exp.state == PromotionState.REJECTED # wait, pit_integrity_ok=False is REJECTED in my code
    # Actually, let's make it INVALID
    adjudicate(exp, [_ev(eid, future_leakage_detected=True)])
    assert exp.state == PromotionState.INVALID
    
    promoted_after = ledger_reader.list_promoted_strategies()
    assert not any(m.experiment_id == eid for m in promoted_after)

def test_canonical_severity_ordering():
    """REGRESSION: INVALID > REJECTED > QUARANTINED > CONDITIONAL > CANARY_ONLY > PROMOTABLE."""
    from strategy_validator.core.enums import BANK_STATE_RANKING
    
    assert BANK_STATE_RANKING[PromotionState.INVALID] > BANK_STATE_RANKING[PromotionState.REJECTED]
    assert BANK_STATE_RANKING[PromotionState.REJECTED] > BANK_STATE_RANKING[PromotionState.QUARANTINED]
    assert BANK_STATE_RANKING[PromotionState.QUARANTINED] > BANK_STATE_RANKING[PromotionState.CONDITIONAL]
    assert BANK_STATE_RANKING[PromotionState.CONDITIONAL] > BANK_STATE_RANKING[PromotionState.CANARY_ONLY]
    assert BANK_STATE_RANKING[PromotionState.CANARY_ONLY] > BANK_STATE_RANKING[PromotionState.PROMOTABLE]
