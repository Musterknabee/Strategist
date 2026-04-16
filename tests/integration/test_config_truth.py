import pytest
import yaml
from datetime import datetime, timezone
from pathlib import Path
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate

def create_mock_experiment():
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
        search_breadth=1,
        decoy_survival_passed=True,
        decoy_suite_version="v1",
        decoy_coverage=1.0
    )
    return ExperimentManifest(
        experiment_id="config-test",
        strategy_name="ConfigTruth",
        version="1.0",
        proposer_id="audit",
        evidence_bundle=bundle
    )

def test_config_threshold_flips_decision():
    """
    CONSTITUTIONAL PROOF: Changing the threshold in promotion_gates.yaml 
    must change the adjudication outcome.
    """
    # Fix path to match load_config's expectation (strategy_validator/promotion_gates.yaml)
    config_path = Path("strategy_validator/promotion_gates.yaml")
    original_content = ""
    if config_path.exists():
        original_content = config_path.read_text()
    
    try:
        payload = {
            "benchmark_id": "SPY",
            "benchmark_version": "v1",
            "benchmark_delta": 0.05,
            "benchmark_passed": True,
            "observed_sharpe": 1.0,
            "sample_size": 252,
            "cpcv_passed": True,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 1.0,
            "cpcv_path_stability": 0.1,
            "incrementality_significant": True,
            "incrementality_p_value": 0.04,  # Marginally below default 0.05
            "pit_integrity_ok": True,
            "alpha_half_life_minutes": 100,
            "expected_latency_minutes": 1,
            "train_sharpes": [1, 2],
            "test_sharpes": [1, 2]
        }
        
        # 1. TEST WITH DEFAULT (0.05) -> Expect PROMOTABLE
        exp1 = create_mock_experiment()
        ev1 = Evidence(
            evidence_id="ev1", experiment_id="config-test", evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            payload=payload, source_module="test", checksum="chk1", timestamp=datetime.now(timezone.utc)
        )
        config_path.write_text("tribunal_thresholds:\n  max_nuisance_p_value: 0.05")
        state1 = adjudicate(exp1, [ev1])
        assert state1 == PromotionState.PROMOTABLE
        
        # 2. TEST WITH STRICTER CONFIG (0.01) -> Expect REJECTED
        exp2 = create_mock_experiment()
        ev2 = Evidence(
            evidence_id="ev2", experiment_id="config-test", evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            payload=payload, source_module="test", checksum="chk2", timestamp=datetime.now(timezone.utc)
        )
        config_path.write_text("tribunal_thresholds:\n  max_nuisance_p_value: 0.01")
        state2 = adjudicate(exp2, [ev2])
        assert state2 == PromotionState.REJECTED
        
        decision = exp2.promotion_history[-1]
        assert any("LACKS_ORTHOGONAL_INCREMENTALITY" in note for note in decision.summary_notes)
        
    finally:
        if original_content:
            config_path.write_text(original_content)
        else:
            config_path.unlink(missing_ok=True)

if __name__ == "__main__":
    pytest.main([__file__])
