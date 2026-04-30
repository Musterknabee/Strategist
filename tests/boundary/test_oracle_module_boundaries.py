from __future__ import annotations

import ast
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
VALIDATOR_DIR = ROOT / "strategy_validator" / "validator"


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


@pytest.mark.boundary
def test_bounded_oracle_modules_do_not_reach_back_into_cli_or_transition_shell() -> None:
    failures: list[str] = []
    for path in VALIDATOR_DIR.glob('oracle*.py'):
        if path.name in {"oracle_transition.py", "__init__.py"}:
            continue
        imports = _module_imports(path)
        if any(name.startswith("strategy_validator.cli") for name in imports):
            failures.append(f"{path.name} imports CLI modules directly")
        if "strategy_validator.validator.oracle_transition" in imports:
            failures.append(f"{path.name} imports oracle_transition.py instead of bounded engines/helpers")
    assert not failures, "\n".join(failures)
