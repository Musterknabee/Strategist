from __future__ import annotations

import ast
from pathlib import Path


def test_ui_backtest_forensics_routes_are_declared_static() -> None:
    tree = ast.parse(Path("strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8"))
    declared = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute) and decorator.func.attr == "get" and decorator.args and isinstance(decorator.args[0], ast.Constant):
                    declared.add((node.name, decorator.args[0].value))
    assert ("get_backtest_forensics", "/backtest-forensics") in declared
    assert ("get_backtest_forensics_latest", "/backtest-forensics/latest") in declared
    assert ("get_backtest_forensics_by_run", "/backtest-forensics/{run_id}") in declared
