from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SHIM = REPO_ROOT / "strategy_validator" / "cli" / "operator_action_event_index.py"


def test_operator_action_event_index_cli_is_compatibility_shim() -> None:
    source = SHIM.read_text(encoding="utf-8")
    tree = ast.parse(source)
    assert "strategy-validator-ledger-ops index-operator-actions" in source
    assert "_ledger_ops_main([\"index-operator-actions\", *args])" in source
    assert "build_operator_action_event_projection_index" not in source
    assert any(isinstance(node, ast.ImportFrom) and node.module == "strategy_validator.cli.ledger_ops" for node in tree.body)
