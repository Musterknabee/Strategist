import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment(search_breadth=1):
    repro = ReproducibilityManifest(
        code_hash="abcdef123456",
        data_snapshot_hash="data-hash",
        universe_hash="univ-hash",
        feature_graph_hash="graph-hash",
        parameter_manifest_hash="param-hash",
        benchmark_version="v1",
        cost_model_version="v1.0",
        calendar_version="v1.0"
    )
    bundle = EvidenceBundle(
        reproducibility=repro,
        benchmark_rung="core-equity",
        search_breadth=search_breadth,
        decoy_survival_passed=True,
        decoy_suite_version="battery-v1",
        decoy_coverage=1.0
    )
    return ExperimentManifest(
        experiment_id=f"exp-{search_breadth}",
        strategy_name="LethalTest",
        version="1.0",
        proposer_id="quant-01",
        state=PromotionState.INVALID,
        evidence_bundle=bundle
    )

def create_evidence(experiment_id, payload):
    return Evidence(
        evidence_id=f"ev-{experiment_id}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="falsification_kernel",
        checksum="checksum123"
    )

def test_dsr_downgrade_on_search_breadth_increase():
    """
    LETHAL TEST: Proves that the orchestrator enforces DSR-based consequences.
    Identical nominal returns are rejected as overfit when context shows high trials.
    """
    # Use a Sharpe that is marginally significant (t ~ 1.58)
    # 0.05 * sqrt(1000) ~ 1.58
    payload = {
        "observed_sharpe": 0.05,  
        "sample_size": 1000,
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.01, # Pass core-equity (min 0.0)
        "benchmark_passed": True,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "incrementality_p_value": 0.001,
        "incrementality_significant": True,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 60,
        "expected_latency_minutes": 5,
        "train_sharpes": [1.0, 2.0, 3.0, 4.0, 5.0],
        "test_sharpes": [1.0, 2.0, 3.0, 4.0, 5.0]
    }

    # CASE A: Low search breadth (benign context)
    experiment_low = create_mock_experiment(search_breadth=1)
    ev_low = create_evidence(experiment_low.experiment_id, payload)
    
    state_low = adjudicate(experiment_low, [ev_low])
    assert state_low == PromotionState.PROMOTABLE
    # DSR should be ~1.58 for trials=1
    assert experiment_low.evidence_bundle.dsr_estimate > 1.0
    
    print(f"Low Breadth (1) State: {state_low}")

    # CASE B: High search breadth (adversarial context)
    experiment_high = create_mock_experiment(search_breadth=10000)
    ev_high = create_evidence(experiment_high.experiment_id, payload)
    
    state_high = adjudicate(experiment_high, [ev_high])
    
    # Must be downgraded due to DSR < 0 gate
    # z_max for 10000 trials is ~3.7. 1.58 < 3.7 => DSR < 0.
    assert state_high == PromotionState.QUARANTINED
    assert experiment_high.evidence_bundle.dsr_estimate < 0.0
    
    print(f"High Breadth (10000) State: {state_high}")
    print(f"Deflated Sharpe: {experiment_high.evidence_bundle.dsr_estimate:.4f}")

def test_latency_decay_gate_enforcement():
    """
    Verifies Gate 4: Rejection of strategies that decay too fast for execution.
    """
    payload = {
        "observed_sharpe": 2.0,
        "sample_size": 504,
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.05,
        "benchmark_passed": True,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "incrementality_significant": True,
        "incrementality_p_value": 0.01,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 7,
        "expected_latency_minutes": 10,
        "train_sharpes": [1.0, 2.0],
        "test_sharpes": [1.0, 2.0]
    }
    
    exp = create_mock_experiment(search_breadth=1)
    ev = create_evidence(exp.experiment_id, payload)
    
    state = adjudicate(exp, [ev])
    assert state == PromotionState.REJECTED

if __name__ == "__main__":
    pytest.main([__file__])
