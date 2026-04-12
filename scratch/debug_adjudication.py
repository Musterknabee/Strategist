from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def debug_adjudication():
    repro = ReproducibilityManifest(
        code_hash="abcdef123456", data_snapshot_hash="data-snapshot-hash", universe_hash="universe-hash",
        feature_graph_hash="feature-graph-hash", parameter_manifest_hash="parameter-hash",
        benchmark_version="bench-v1", cost_model_version="v1.0", calendar_version="v1.0"
    )
    bundle = EvidenceBundle(
        reproducibility=repro, benchmark_rung="L1", search_breadth=1,
        decoy_survival_passed=True, decoy_suite_version="v1", decoy_coverage=1.0
    )
    experiment = ExperimentManifest(
        experiment_id="debug-123", strategy_name="DebugStrat", version="1.0",
        proposer_id="audit", evidence_bundle=bundle
    )
    
    payload = {
        "benchmark_id": "SPY", "benchmark_version": "bench-v1",
        "benchmark_delta": 0.40, "benchmark_passed": True,
        "requires_shorting": True, "borrow_available": True,
        "borrow_cost_bps": 300, "pit_integrity_ok": True,
        "observed_sharpe": 2.5, "sample_size": 250,
        "train_sharpes": [1, 1], "test_sharpes": [1, 1],
        "incrementality_p_value": 0.001,
        "cpcv_passed": True, "cpcv_folds": 5, "cpcv_path_coverage": 1.0
    }
    
    evidence = Evidence(
        evidence_id="ev-123", experiment_id="debug-123",
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        payload=payload, source_module="audit", checksum="chk",
        timestamp=datetime.now(timezone.utc)
    )
    
    res = adjudicate(experiment, [evidence])
    print(f"Final State: {res}")
    decision = experiment.promotion_history[-1]
    for gate in decision.gate_results:
        print(f"Gate: {gate.gate_name}, Passed: {gate.passed}, Reason: {gate.reason}")

if __name__ == "__main__":
    debug_adjudication()
