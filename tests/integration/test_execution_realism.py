import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment(rung="core-equity"):
    # Use benchmark_version consistent with the L1 rung registry entry ("bench-v1")
    bench_version = "bench-v1" if rung == "L1" else "v1"
    repro = ReproducibilityManifest(
        code_hash="abcdef123456",
        data_snapshot_hash="data-hash",
        universe_hash="univ-hash",
        feature_graph_hash="graph-hash",
        parameter_manifest_hash="param-hash",
        benchmark_version=bench_version,
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
        experiment_id=f"realism-{datetime.now().timestamp()}",
        strategy_name="ExecutionRealismTest",
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

def test_strategy_fails_on_post_cost_delta():
    """
    REALISM LAW: Beating benchmark pre-cost but failing post-cost must be REJECTED.
    """
    experiment = create_mock_experiment(rung="L1")
    
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "bench-v1",
        "benchmark_delta": 0.0150,
        "benchmark_passed": True,
        "spread_bps": 40.0,
        "slippage_bps": 20.0,
        "observed_sharpe": 1.0,
        "sample_size": 100,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 1000,
        "expected_latency_minutes": 1,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    
    decision = experiment.promotion_history[-1]
    report = decision.benchmark_report
    assert report.passed is False
    assert "INSUFFICIENT_POST_COST_DELTA" in report.failure_reason
    assert report.post_cost_excess_metric == pytest.approx(0.0090)

def test_midpoint_only_is_quarantined():
    """
    REALISM LAW: Midpoint-only economics can never produce PROMOTABLE.
    """
    experiment = create_mock_experiment()
    payload = {
        "benchmark_id": "SPY",
        "benchmark_version": "v1",
        "benchmark_delta": 0.10,
        "benchmark_passed": True,
        "economics_model": "midpoint_only", # Correct key from cost_engine
        "observed_sharpe": 1.0, "sample_size": 100,
        "pit_integrity_ok": True,
        "alpha_half_life_minutes": 1000, "expected_latency_minutes": 1,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    adjudicate(experiment, [create_evidence(experiment.experiment_id, payload)])
    
    assert experiment.state == PromotionState.REJECTED
    
    decision = experiment.promotion_history[-1]
    exec_report = decision.execution_report
    assert exec_report.midpoint_only_flag is True
    assert exec_report.passed is False

if __name__ == "__main__":
    pytest.main([__file__])
