import ast
from pathlib import Path


def _contains_forbidden_tribunal_calls_or_imports(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("strategy_validator.validator.orchestrator"):
                return True
            if node.module.startswith("strategy_validator.ledger.writer"):
                return True
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("strategy_validator.validator.orchestrator"):
                    return True
                if n.name.startswith("strategy_validator.ledger.writer"):
                    return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"adjudicate", "commit_state_transition"}:
                return True
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    name = node.args[0].value
                    if name.startswith("strategy_validator.validator.orchestrator"):
                        return True
                    if name.startswith("strategy_validator.ledger.writer"):
                        return True
            if isinstance(node.func, ast.Attribute):
                if node.func.attr in {"adjudicate", "commit_state_transition"}:
                    return True
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        name = node.args[0].value
                        if name.startswith("strategy_validator.validator.orchestrator"):
                            return True
                        if name.startswith("strategy_validator.ledger.writer"):
                            return True
    return False


def test_tribunal_has_no_adjudication_or_ledger_write_surface() -> None:
    tribunal_root = Path(__file__).resolve().parents[2] / "strategy_validator" / "tribunal"
    for path in tribunal_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        assert _contains_forbidden_tribunal_calls_or_imports(path) is False, (
            f"Constitutional violation: tribunal contains adjudication/write surface in {path}"
        )


def test_tribunal_mutation_detector_flags_adjudicate_call(tmp_path: Path) -> None:
    sample = tmp_path / "tribunal_rogue_call.py"
    sample.write_text("def f(x):\n    return adjudicate(x, [])\n", encoding="utf-8")
    assert _contains_forbidden_tribunal_calls_or_imports(sample) is True


def test_tribunal_mutation_detector_flags_importlib_dynamic_import(tmp_path: Path) -> None:
    sample = tmp_path / "tribunal_rogue_importlib.py"
    sample.write_text(
        "\n".join(
            [
                "import importlib",
                "importlib.import_module('strategy_validator.ledger.writer')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_tribunal_calls_or_imports(sample) is True


def test_tribunal_mutation_detector_flags_dunder_import(tmp_path: Path) -> None:
    sample = tmp_path / "tribunal_rogue_dunder.py"
    sample.write_text("__import__('strategy_validator.validator.orchestrator')\n", encoding="utf-8")
    assert _contains_forbidden_tribunal_calls_or_imports(sample) is True
