from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path("strategy_validator/application")


def _source(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def _function_names(path: str) -> set[str]:
    tree = ast.parse(_source(path))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_workboard_intelligence_board_facade_remains_thin() -> None:
    source = _source("ui_workboard_intelligence_board.py")
    assert len(source.splitlines()) <= 60
    assert "def _build_board_governance_digest(" not in source
    assert "def _build_board_materialization_status(" not in source
    assert "ui_workboard_intelligence_board_governance" in source
    assert "ui_workboard_intelligence_board_briefing" in source
    assert "ui_workboard_intelligence_board_materialization" in source


def test_workboard_intelligence_board_subphase_ownership() -> None:
    assert _function_names("ui_workboard_intelligence_board_governance.py") == {
        "_build_board_governance_snapshot",
        "_build_board_governance_clusters",
        "_build_board_governance_digest",
    }
    assert _function_names("ui_workboard_intelligence_board_briefing.py") == {
        "_build_board_evidence_briefing",
        "_build_board_operator_brief",
    }
    assert _function_names("ui_workboard_intelligence_board_materialization.py") == {
        "_build_board_materialization_status",
    }


def test_workboard_intelligence_board_facade_exports_match_subphases() -> None:
    from strategy_validator.application import ui_workboard_intelligence_board as facade
    from strategy_validator.application import ui_workboard_intelligence_board_briefing as briefing
    from strategy_validator.application import ui_workboard_intelligence_board_governance as governance
    from strategy_validator.application import ui_workboard_intelligence_board_materialization as materialization

    expected = [
        governance.__all__[0],
        briefing.__all__[0],
        governance.__all__[1],
        governance.__all__[2],
        materialization.__all__[0],
        briefing.__all__[1],
    ]
    assert facade.__all__ == expected
    for name in expected:
        assert getattr(facade, name) is not None


def test_workboard_intelligence_runtime_keeps_legacy_board_import_path() -> None:
    source = _source("ui_workboard_intelligence.py")
    assert "strategy_validator.application.ui_workboard_intelligence_board" in source
    assert "ui_workboard_intelligence_board_governance" not in source
    assert "ui_workboard_intelligence_board_materialization" not in source
