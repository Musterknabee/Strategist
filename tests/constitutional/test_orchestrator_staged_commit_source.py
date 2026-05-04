from __future__ import annotations

from pathlib import Path


def test_orchestrator_stages_mutations_until_ledger_commit_succeeds() -> None:
    source = Path("strategy_validator/validator/orchestrator/__init__.py").read_text(encoding="utf-8")
    assert "working_experiment = experiment.model_copy(deep=True)" in source
    assert "commit_state_transition(working_experiment" in source
    assert source.index("commit_state_transition(working_experiment") < source.index("experiment.state = working_experiment.state")
