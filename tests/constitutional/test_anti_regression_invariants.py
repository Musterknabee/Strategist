from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
def test_priority_zero_runtime_roots_are_not_missing_again():
    for rel in ["strategy_validator/validator/readiness.py","strategy_validator/validator/orchestrator/__init__.py","strategy_validator/validator/services/decision_service.py","strategy_validator/validator/services/promotion_commit_service.py","strategy_validator/validator/services/integrity_gate_service.py","strategy_validator/api/routes/__init__.py"]:
        assert (ROOT/rel).exists(), rel
def test_validator_orchestrator_is_the_only_ledger_authority_named_by_writer():
    writer=(ROOT/"strategy_validator/ledger/writer/__init__.py").read_text(); orch=(ROOT/"strategy_validator/validator/orchestrator/__init__.py").read_text()
    assert '_ORCHESTRATOR_MODULE = "strategy_validator.validator.orchestrator"' in writer
    assert "issue_write_authority()" in orch and "commit_state_transition" in orch
