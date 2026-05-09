from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "strategy_validator" / "application"


def _line_count(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").splitlines())


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_daily_operator_run_projection_no_longer_owns_paper_execution_component() -> None:
    projection = APP / "daily_operator_run_projection.py"

    assert _line_count(projection) <= 140
    assert "_paper_execution" not in _function_names(projection)


def test_daily_operator_run_component_helpers_and_paper_execution_are_extracted() -> None:
    common = _function_names(APP / "daily_operator_run_common.py")
    paper = _function_names(APP / "daily_operator_run_paper_execution.py")

    assert {"_as_dict", "_as_list", "_strings", "_int", "_safe", "_component"} <= common
    assert "_paper_execution" in paper


def test_daily_operator_run_legacy_import_surface_remains_stable() -> None:
    facade = importlib.import_module("strategy_validator.application.daily_operator_run_projection")

    assert callable(facade.build_ui_daily_operator_run_payload)
    assert callable(facade._paper_execution)
