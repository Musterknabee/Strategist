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
        experiment_id=f"exp-{search_breadth}-{datetime.now().timestamp()}",
        strategy_name="ProsecutionTest",
        version="1.0",
        proposer_id="quant-audit",
        state=PromotionState.PROMOTABLE,
        evidence_bundle=bundle
    )

def create_evidence(experiment_id, payload):
    return Evidence(
        evidence_id=f"ev-{experiment_id}",
        experiment_id=experiment_id,
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="audit_sensor",
        checksum="audit-chk"
    )

def test_rejection_records_fatal_gate_provenance():
    """
    Verify that a rejection due to alpha decay is recorded in the promotion history.
    """
    experiment = create_mock_experiment()
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.05,
        "benchmark_passed": True,
        "observed_sharpe": 2.0,
        "sample_size": 1000,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "incrementality_significant": True,
        "incrementality_p_value": 0.01,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 5,
        "expected_latency_minutes": 5,
        "train_sharpes": [1, 2, 3],
        "test_sharpes": [1, 2, 3]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    
    history = experiment.promotion_history
    assert len(history) >= 1
    decision = history[-1]
    
    exec_gate = next(g for g in decision.gate_results if g.gate_name == "ExecutionRealism")
    assert exec_gate.passed is False
    assert "latency" in (exec_gate.reason or "").lower() or "half-life" in (exec_gate.reason or "").lower()

def test_quarantine_records_dsr_provenance():
    """
    Verify that a DSR-based quarantine is recorded with metric values.
    """
    experiment = create_mock_experiment(search_breadth=100000)
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.05,
        "benchmark_passed": True,
        "observed_sharpe": 0.01,
        "sample_size": 500,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "incrementality_significant": True,
        "incrementality_p_value": 0.01,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 100,
        "expected_latency_minutes": 1,
        "train_sharpes": [1, 2],
        "test_sharpes": [1, 2]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.QUARANTINED
    
    decision = experiment.promotion_history[-1]
    robust_gate = next(g for g in decision.gate_results if g.gate_name == "RobustnessAudit")
    assert robust_gate.passed is False

def test_promotable_requires_all_gates_pass():
    """
    Verify a PROMOTABLE decision certifies all required gates.
    """
    experiment = create_mock_experiment(search_breadth=1)
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.10,
        "benchmark_passed": True,
        "observed_sharpe": 3.0,
        "sample_size": 1000,
        "cpcv_passed": True,
        "cpcv_folds": 5,
        "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1,
        "incrementality_significant": True,
        "incrementality_p_value": 0.001,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 500,
        "expected_latency_minutes": 1,
        "train_sharpes": [1, 2, 3, 4, 5],
        "test_sharpes": [1, 2, 3, 4, 5]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.PROMOTABLE
    
    decision = experiment.promotion_history[-1]
    for gate in decision.gate_results:
        if gate.gate_name in ["FutureLeakage", "BenchmarkSuccess", "RobustnessAudit", "ExecutionRealism"]:
            assert gate.passed is True

if __name__ == "__main__":
    pytest.main([__file__])
