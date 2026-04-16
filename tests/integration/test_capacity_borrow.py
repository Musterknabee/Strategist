import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment(rung="core-equity"):
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
        benchmark_rung=rung,
        search_breadth=1,
        decoy_survival_passed=True,
        decoy_suite_version="v1",
        decoy_coverage=1.0
    )
    return ExperimentManifest(
        experiment_id=f"capacity-{datetime.now().timestamp()}",
        strategy_name="CapacityBorrowTest",
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

def test_participation_scaling_rejects_excessive_size():
    """
    CAPACITY LAW: Excessive participation rate must trigger failure.
    """
    experiment = create_mock_experiment(rung="core-equity")
    
    # 15% participation is over the 10% hard-cap
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.05,
        "benchmark_passed": True,
        "estimated_participation_rate": 0.15, 
        "observed_sharpe": 1.0, "sample_size": 100,
        "pit_integrity_ok": True,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    decision = experiment.promotion_history[-1]
    assert "EXCESSIVE_PARTICIPATION" in decision.execution_report.failure_reason

def test_nonlinear_impact_erases_alpha():
    """
    CAPACITY LAW: Nonlinear impact from participation must degrade post-cost returns.
    """
    experiment = create_mock_experiment(rung="core-equity") # Requires 0.0 delta
    
    # 0.5% (50bps) pre-cost alpha. 
    # At 5% participation, sqrt(0.05) * 600bps ~ 134bps impact.
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.0050, 
        "benchmark_passed": True,
        "estimated_participation_rate": 0.05, 
        "pit_integrity_ok": True,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    # Pre-cost 50bps - 134bps impact = -84bps < 0 threshold.
    assert experiment.state == PromotionState.REJECTED
    decision = experiment.promotion_history[-1]
    assert decision.execution_report.nonlinear_impact_bps > 100

def test_borrow_unavailability_is_fatal():
    """
    BORROW LAW: If shorting is required and borrow is unavailable, state is REJECTED.
    """
    experiment = create_mock_experiment()
    payload = {
        "benchmark_id": "SPY", "benchmark_version": "v1",
        "benchmark_delta": 0.10, "benchmark_passed": True,
        "requires_shorting": True,
        "borrow_available": False, # Fatal
        "pit_integrity_ok": True,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    decision = experiment.promotion_history[-1]
    assert decision.execution_report.shortability_passed is False
    assert decision.execution_report.borrow_constraint_note == "BORROW_UNAVAILABLE"

if __name__ == "__main__":
    pytest.main([__file__])
