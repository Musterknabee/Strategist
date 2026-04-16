"""Static checks: ledger commit helper is not invoked outside the orchestration path."""

from __future__ import annotations

import ast
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG = REPO_ROOT / "strategy_validator"

_ALLOWED = {
    PKG / "ledger" / "writer" / "__init__.py",
    PKG / "validator" / "orchestrator" / "__init__.py",
}


def _contains_forbidden_commit_call(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "commit_state_transition":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "commit_state_transition":
                return True
    return False


def test_commit_state_transition_only_allowed_files() -> None:
    for path in PKG.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        if path in _ALLOWED:
            continue
        if _contains_forbidden_commit_call(path):
            raise AssertionError(
                f"Constitutional violation: commit_state_transition call site in {path}"
            )


def test_commit_state_transition_detector_flags_direct_calls(tmp_path: Path) -> None:
    sample = tmp_path / "rogue_call.py"
    sample.write_text(
        "\n".join(
            [
                "def rogue(experiment):",
                "    commit_state_transition(experiment)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_commit_call(sample) is True


def test_commit_state_transition_detector_flags_attribute_calls(tmp_path: Path) -> None:
    sample = tmp_path / "rogue_attr_call.py"
    sample.write_text(
        "\n".join(
            [
                "def rogue(mod, experiment):",
                "    mod.commit_state_transition(experiment)",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_commit_call(sample) is True
