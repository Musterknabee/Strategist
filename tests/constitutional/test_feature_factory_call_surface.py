import ast
from pathlib import Path


def _contains_forbidden_feature_factory_surface(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("strategy_validator.validator"):
                return True
            if node.module.startswith("strategy_validator.tribunal"):
                return True
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("strategy_validator.validator"):
                    return True
                if n.name.startswith("strategy_validator.tribunal"):
                    return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in {"adjudicate"}:
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr in {"adjudicate"}:
                return True
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    name = node.args[0].value
                    if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.tribunal"):
                        return True
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        name = node.args[0].value
                        if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.tribunal"):
                            return True
    return False


def test_feature_factory_has_no_validator_or_tribunal_surface() -> None:
    ff_root = Path(__file__).resolve().parents[2] / "strategy_validator" / "feature_factory"
    for path in ff_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        assert _contains_forbidden_feature_factory_surface(path) is False, (
            f"Constitutional violation: feature_factory has forbidden surface in {path}"
        )


def test_feature_factory_mutation_detector_flags_validator_import(tmp_path: Path) -> None:
    sample = tmp_path / "ff_rogue.py"
    sample.write_text("from strategy_validator.validator.orchestrator import adjudicate\n", encoding="utf-8")
    assert _contains_forbidden_feature_factory_surface(sample) is True


def test_feature_factory_mutation_detector_flags_importlib_bypass(tmp_path: Path) -> None:
    sample = tmp_path / "ff_rogue_importlib.py"
    sample.write_text(
        "\n".join(
            [
                "import importlib",
                "importlib.import_module('strategy_validator.tribunal')",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_feature_factory_surface(sample) is True


def test_feature_factory_mutation_detector_flags_dunder_import_bypass(tmp_path: Path) -> None:
    sample = tmp_path / "ff_rogue_dunder.py"
    sample.write_text("__import__('strategy_validator.validator')\n", encoding="utf-8")
    assert _contains_forbidden_feature_factory_surface(sample) is True
