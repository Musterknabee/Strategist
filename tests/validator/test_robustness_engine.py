import pytest
from datetime import datetime, timezone
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import PromotionState, EvidenceType
from strategy_validator.validator.robustness.engine import RobustnessEngine

def create_test_evidence(payload):
    return Evidence(
        evidence_id="test-ev",
        experiment_id="test-exp",
        evidence_type=EvidenceType.OUT_OF_SAMPLE_AUDIT,
        timestamp=datetime.now(timezone.utc),
        payload=payload,
        source_module="test_source",
        checksum="8bb2abcd1234"
    )

def test_robustness_gate_failure_on_low_coverage():
    engine = RobustnessEngine()
    
    evidence = [
        create_test_evidence({
            "cpcv_passed": False,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 0.5,
            "cpcv_path_stability": 0.2
        })
    ]
    
    report = engine.evaluate(evidence)
    assert report.passed is False
    assert report.suggested_state == PromotionState.REJECTED
    assert any("INSUFFICIENT_PATH_COVERAGE" in note for note in report.evaluation_notes)

def test_robustness_gate_quarantine_on_high_instability():
    engine = RobustnessEngine()
    
    evidence = [
        create_test_evidence({
            "cpcv_passed": True,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 0.9,
            "cpcv_path_stability": 1.5
        })
    ]
    
    report = engine.evaluate(evidence)
    assert report.passed is False
    assert report.suggested_state == PromotionState.QUARANTINED
    assert any("UNSTABLE_FOLD_OUTCOMES" in note for note in report.evaluation_notes)

def test_robustness_gate_failure_on_insignificant_incrementality():
    engine = RobustnessEngine()
    
    evidence = [
        create_test_evidence({
            "cpcv_passed": True,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 1.0,
            "cpcv_path_stability": 0.1,
            "incrementality_p_value": 0.45,
            "incrementality_significant": False
        })
    ]
    
    report = engine.evaluate(evidence)
    assert report.passed is False
    assert report.suggested_state == PromotionState.REJECTED
    assert any("LACKS_ORTHOGONAL_INCREMENTALITY" in note for note in report.evaluation_notes)

def test_robustness_gate_canary_when_no_incrementality_test():
    engine = RobustnessEngine()
    
    evidence = [
        create_test_evidence({
            "cpcv_passed": True,
            "cpcv_folds": 5,
            "cpcv_path_coverage": 1.0,
            "cpcv_path_stability": 0.1
        })
    ]
    
    report = engine.evaluate(evidence)
    assert report.suggested_state == PromotionState.CONDITIONAL # PBO/DSR missing
    assert any("INCREMENTALITY_NOT_TESTED" in note for note in report.evaluation_notes)
