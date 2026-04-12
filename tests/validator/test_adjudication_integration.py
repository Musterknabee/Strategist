import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment():
    repro = ReproducibilityManifest(
        code_hash="abcdef123456",
        data_snapshot_hash="data-hash-val",
        universe_hash="univ-hash-val",
        feature_graph_hash="graph-hash-val",
        parameter_manifest_hash="param-hash-val",
        benchmark_version="v1", # Matching 'core-equity'
        cost_model_version="v1.0",
        calendar_version="v1.0"
    )
    bundle = EvidenceBundle(
        reproducibility=repro,
        benchmark_rung="core-equity",
        search_breadth=10
    )
    return ExperimentManifest(
        experiment_id="exp-001",
        strategy_name="TestStrategy",
        version="1.0.0",
        proposer_id="proposer-abc",
        state=PromotionState.INVALID,
        evidence_bundle=bundle
    )

def create_evidence(payload, ev_id="ev-123"):
    return Evidence(
        evidence_id=ev_id,
        experiment_id="exp-001",
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="test_source",
        checksum="8bb2abcd1234"
    )

def test_robustness_rejection_blocks_promotion():
    experiment = create_mock_experiment()
    
    # Evidence matches 'core-equity' (SPY, v1)
    evidence = [
        create_evidence({
            "benchmark_id": "SPY",
            "benchmark_version": "v1",
            "benchmark_delta": 0.05, 
            "benchmark_passed": True,
            "cpcv_passed": False,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 0.5, # FAIL
            "cpcv_path_stability": 0.1,
            "incrementality_p_value": 0.01,
            "incrementality_significant": True,
            "observed_sharpe": 1.5,
            "sample_size": 1000,
            "train_sharpes": [1.0],
            "test_sharpes": [1.0]
        }),
        create_evidence({
            "pit_integrity_ok": True
        }, ev_id="ev-2")
    ]
    
    state = adjudicate(experiment, evidence)
    assert state == PromotionState.REJECTED
    assert experiment.evidence_bundle.cpcv_passed is False

def test_missing_robustness_prevents_promotable():
    experiment = create_mock_experiment()
    
    evidence = [
        create_evidence({
            "benchmark_id": "SPY",
            "benchmark_version": "v1",
            "benchmark_delta": 0.05,
            "benchmark_passed": True,
            "observed_sharpe": 1.5,
            "sample_size": 1000,
            "train_sharpes": [1.0],
            "test_sharpes": [1.0]
        })
    ]
    
    state = adjudicate(experiment, evidence)
    assert state != PromotionState.PROMOTABLE

def test_quarantine_preserved_on_instability():
    experiment = create_mock_experiment()
    experiment.evidence_bundle.decoy_survival_passed = True
    experiment.evidence_bundle.decoy_suite_version = "decoy-v1"
    experiment.evidence_bundle.decoy_coverage = 1.0

    evidence = [
        create_evidence({
            "benchmark_id": "SPY",
            "benchmark_version": "v1",
            "benchmark_delta": 0.05,
            "benchmark_passed": True,
            "cpcv_passed": True,
            "cpcv_folds": 10,
            "cpcv_path_coverage": 1.0,
            "cpcv_path_stability": 1.5, # instability
            "incrementality_p_value": 0.01,
            "incrementality_significant": True,
            "observed_sharpe": 1.5,
            "sample_size": 1000,
            "train_sharpes": [1.0],
            "test_sharpes": [1.0]
        })
    ]
    
    state = adjudicate(experiment, evidence)
    assert state == PromotionState.QUARANTINED

if __name__ == "__main__":
    pytest.main([__file__])
