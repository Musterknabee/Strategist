from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_workboard_intelligence_policy_facade_remains_thin() -> None:
    source = _source("ui_workboard_intelligence_policy.py")
    assert len(source.splitlines()) <= 60
    assert "def _build_policy_recommendation(" not in source
    assert "ui_workboard_intelligence_policy_provenance" in source
    assert "ui_workboard_intelligence_policy_commands" in source
    assert "ui_workboard_intelligence_policy_briefing" in source
    assert "ui_workboard_intelligence_policy_recommendation" in source


def test_workboard_intelligence_policy_subphase_ownership() -> None:
    assert _function_names("ui_workboard_intelligence_policy_provenance.py") == {
        "_build_action_provenance",
    }
    assert _function_names("ui_workboard_intelligence_policy_commands.py") == {
        "_action_precondition_state",
        "_build_command_readiness",
        "_command_item",
    }
    assert _function_names("ui_workboard_intelligence_policy_briefing.py") == {
        "_build_operator_brief",
        "_build_evidence_backed_briefing",
    }
    assert _function_names("ui_workboard_intelligence_policy_recommendation.py") == {
        "_append_policy_signal",
        "_build_policy_recommendation",
    }


def test_workboard_intelligence_policy_facade_exports_match_subphases() -> None:
    from strategy_validator.application import ui_workboard_intelligence_policy as facade
    from strategy_validator.application import ui_workboard_intelligence_policy_briefing as briefing
    from strategy_validator.application import ui_workboard_intelligence_policy_commands as commands
    from strategy_validator.application import ui_workboard_intelligence_policy_provenance as provenance
    from strategy_validator.application import ui_workboard_intelligence_policy_recommendation as recommendation

    expected = [
        *provenance.__all__,
        *commands.__all__,
        *briefing.__all__,
        *recommendation.__all__,
    ]
    assert facade.__all__ == expected
    for name in expected:
        assert getattr(facade, name) is not None


def test_workboard_intelligence_runtime_keeps_legacy_policy_import_path() -> None:
    source = _source("ui_workboard_intelligence.py")
    assert "strategy_validator.application.ui_workboard_intelligence_policy" in source
    assert "ui_workboard_intelligence_policy_recommendation" not in source
