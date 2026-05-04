from __future__ import annotations

import ast
from pathlib import Path


def test_ui_daily_operator_run_routes_are_declared_static() -> None:
    tree = ast.parse(Path("strategy_validator/api/routes/ui_routes_detail_runtime.py").read_text(encoding="utf-8"))
    declared: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr != "get":
                continue
            if not decorator.args or not isinstance(decorator.args[0], ast.Constant):
                continue
            path = decorator.args[0].value
            if isinstance(path, str):
                declared.add((node.name, path))
    assert ("get_daily_operator_run", "/daily-operator-run") in declared
    assert ("get_daily_operator_run_latest", "/daily-operator-run/latest") in declared


def test_facade_lists_daily_operator_run_routes() -> None:
    from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory
    inv = build_ui_public_facade_inventory()
    paths = {r["path"] if isinstance(r, dict) else getattr(r, "path", "") for r in inv["routes"]}
    assert "/ui/daily-operator-run" in paths
    assert "/ui/daily-operator-run/latest" in paths
