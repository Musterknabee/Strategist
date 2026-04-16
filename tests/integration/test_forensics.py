import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest, compute_config_hash
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.ledger._append_only import read_latest_event, read_events

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
        experiment_id=f"forensic-{datetime.now().timestamp()}",
        strategy_name="ForensicHardening",
        version="1.0",
        proposer_id="forensic-officer",
        evidence_bundle=bundle
    )

def test_adjudication_config_sealing():
    """
    Ensures that the specific configuration thresholds used for a decision 
    are snapped and hashed into the ledged record.
    """
    # 1. SETUP
    config_path = Path("strategy_validator/promotion_gates.yaml")
    original_content = config_path.read_text() if config_path.exists() else ""
    
    try:
        payload = {
            "benchmark_id": "SPY", "benchmark_version": "v1", "benchmark_delta": 0.05,
            "benchmark_passed": True, "observed_sharpe": 1.0, "sample_size": 100,
            "cpcv_passed": True, "cpcv_folds": 5, "cpcv_path_coverage": 1.0,
            "cpcv_path_stability": 0.1, "incrementality_significant": True,
            "incrementality_p_value": 0.01, "pit_integrity_ok": True,
            "alpha_half_life_minutes": 100, "expected_latency_minutes": 1,
            "train_sharpes": [1], "test_sharpes": [1]
        }
        
        # 2. ADJUDICATE WITH CONFIG A
        config_path.write_text("tribunal_thresholds:\n  max_nuisance_p_value: 0.05")
        exp1 = create_mock_experiment()
        ev1 = Evidence(
            evidence_id="ev1", experiment_id=exp1.experiment_id, evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            payload=payload, source_module="test", checksum="chk1", timestamp=datetime.now(timezone.utc)
        )
        adjudicate(exp1, [ev1])
        
        event1 = read_latest_event(exp1.experiment_id)
        decision1 = event1.event_payload["promotion_history"][-1]
        hash1 = decision1["config_hash"]
        assert hash1 is not None
        
        # 3. ADJUDICATE WITH CONFIG B (Different threshold)
        config_path.write_text("tribunal_thresholds:\n  max_nuisance_p_value: 0.04")
        exp2 = create_mock_experiment()
        ev2 = Evidence(
            evidence_id="ev2", experiment_id=exp2.experiment_id, evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
            payload=payload, source_module="test", checksum="chk2", timestamp=datetime.now(timezone.utc)
        )
        adjudicate(exp2, [ev2])
        
        event2 = read_latest_event(exp2.experiment_id)
        decision2 = event2.event_payload["promotion_history"][-1]
        hash2 = decision2["config_hash"]
        
        # PROOF: Config hash differs due to threshold change
        assert hash1 != hash2
        print(f"Config Hash A: {hash1[:8]}...")
        print(f"Config Hash B: {hash2[:8]}...")

    finally:
        if original_content: config_path.write_text(original_content)
        else: config_path.unlink(missing_ok=True)

def test_ledger_chain_integrity():
    """
    Verifies that the ledger uses structural chaining (previous_event_hash).
    """
    exp = create_mock_experiment()
    payload = {
        "benchmark_id": "SPY", "benchmark_version": "v1", "benchmark_delta": 0.05,
        "benchmark_passed": True, "observed_sharpe": 1.0, "sample_size": 100,
        "cpcv_passed": True, "cpcv_folds": 5, "cpcv_path_coverage": 1.0,
        "cpcv_path_stability": 0.1, "incrementality_significant": True,
        "incrementality_p_value": 0.01, "pit_integrity_ok": True,
        "alpha_half_life_minutes": 100, "expected_latency_minutes": 1,
        "train_sharpes": [1], "test_sharpes": [1]
    }
    
    # Adjudicate Twice
    ev1 = Evidence(
        evidence_id="ev_a", experiment_id=exp.experiment_id, evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        payload=payload, source_module="test", checksum="chk_a", timestamp=datetime.now(timezone.utc)
    )
    adjudicate(exp, [ev1])
    
    ev2 = Evidence(
        evidence_id="ev_b", experiment_id=exp.experiment_id, evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        payload=payload, source_module="test", checksum="chk_b", timestamp=datetime.now(timezone.utc)
    )
    adjudicate(exp, [ev2])
    
    events = read_events(exp.experiment_id)
    assert len(events) == 2
    
    # CHAIN PROOF: Event 2 points to Event 1's hash
    assert events[1].previous_event_hash == events[0].event_hash
    assert events[1].sequence_number == events[0].sequence_number + 1

if __name__ == "__main__":
    pytest.main([__file__])
