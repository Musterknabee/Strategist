import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment(rung="core-equity"):
    repro = ReproducibilityManifest(
        code_hash="abcdef123456",
        data_snapshot_hash="data-snapshot-hash",
        universe_hash="universe-hash",
        feature_graph_hash="feature-graph-hash",
        parameter_manifest_hash="parameter-hash",
        benchmark_version="bench-v1",
        cost_model_version="v1.0",
        calendar_version="v1.0"
    )
    bundle = EvidenceBundle(
        reproducibility=repro,
        benchmark_rung=rung,
        search_breadth=1,
        decoy_survival_passed=True,
        decoy_suite_version="v1",
        decoy_coverage=1.0
    )
    return ExperimentManifest(
        experiment_id=f"stress-{datetime.now().timestamp()}",
        strategy_name="ExecutionStressTest",
        version="1.0",
        proposer_id="audit",
        evidence_bundle=bundle
    )

def create_evidence(experiment_id, payload):
    return Evidence(
        evidence_id=f"ev-{experiment_id}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        payload=payload,
        source_module="audit",
        checksum="chk",
        timestamp=datetime.now(timezone.utc)
    )

def test_adverse_liquidity_stress_degrades_state():
    """
    STRESS LAW: Passing baseline but failing 4x borrow cost stress must degrade state.
    """
    # Use L1 which has benchmark_version bench-v1 in registry
    experiment = create_mock_experiment(rung="L1")
    
    payload = {
        "benchmark_id": "SPY", "benchmark_version": "bench-v1",
        "benchmark_delta": 0.30, "benchmark_passed": True,
        "requires_shorting": True,
        "borrow_available": True,
        "borrow_cost_bps": 300, # Baseline PASS (300 < 500)
                                # Stress = 300 * 4 = 1200 > 1000 threshold -> FAIL
        "pit_integrity_ok": True,
        # Mock Robustness to avoid REJECTED from engine
        "observed_sharpe": 2.0, "sample_size": 200,
        "train_sharpes": [1], "test_sharpes": [1],
        "incremental_p_value": 0.001,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "dsr_passed": True
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    # Adjudication logic: 
    # ExecutionStressResilience: passed=False -> state = PromotionState.REJECTED
    assert experiment.state == PromotionState.REJECTED
    decision = experiment.promotion_history[-1]
    assert decision.execution_report.stress_report.passed is False
    assert "ADVERSE_LIQUIDITY" in decision.execution_report.stress_report.failure_reason

def test_borrow_recall_risk_is_fatal():
    """
    STRESS LAW: High recall risk for short-side strategy is REJECTED.
    """
    experiment = create_mock_experiment(rung="L1")
    payload = {
        "benchmark_id": "SPY", "benchmark_version": "bench-v1",
        "benchmark_delta": 0.10, "benchmark_passed": True,
        "requires_shorting": True,
        "borrow_available": True,
        "borrow_recall_risk": True, # Fatal stress
        "pit_integrity_ok": True,
        "train_sharpes": [1], "test_sharpes": [1],
        "incremental_p_value": 0.001, 
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    decision = experiment.promotion_history[-1]
    assert "RECALL_RISK" in decision.execution_report.stress_report.failure_reason

if __name__ == "__main__":
    pytest.main([__file__])
