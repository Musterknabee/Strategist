import ast
from pathlib import Path


def _contains_forbidden_proposer_surface(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("strategy_validator.validator"):
                return True
            if node.module.startswith("strategy_validator.ledger"):
                return True
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("strategy_validator.validator"):
                    return True
                if n.name.startswith("strategy_validator.ledger"):
                    return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"adjudicate", "commit_state_transition"}:
                return True
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    name = node.args[0].value
                    if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.ledger"):
                        return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"adjudicate", "commit_state_transition"}:
                return True
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        name = node.args[0].value
                        if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.ledger"):
                            return True
    return False


def test_proposers_have_no_validator_or_ledger_surface() -> None:
    root = Path(__file__).resolve().parents[2] / "strategy_validator" / "proposers"
    for path in root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        assert _contains_forbidden_proposer_surface(path) is False, (
            f"Constitutional violation: proposers contain forbidden surface in {path}"
        )


def test_proposers_mutation_detector_flags_importlib_bypass(tmp_path: Path) -> None:
    sample = tmp_path / "proposer_rogue.py"
    sample.write_text(
        "\n".join(
            [
                "import importlib",
                "importlib.import_module('strategy_validator.validator.orchestrator')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_proposer_surface(sample) is True


def test_proposers_mutation_detector_flags_dunder_import_bypass(tmp_path: Path) -> None:
    sample = tmp_path / "proposer_rogue_dunder.py"
    sample.write_text("__import__('strategy_validator.ledger.writer')\n", encoding="utf-8")
    assert _contains_forbidden_proposer_surface(sample) is True
