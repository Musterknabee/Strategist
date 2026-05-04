import ast
from pathlib import Path


def _api_module_violates_transport_thinness(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("strategy_validator.validator"):
                return True
            if node.module.startswith("strategy_validator.ledger.writer"):
                return True
        if isinstance(node, ast.Import):
            for n in node.names:
                if n.name.startswith("strategy_validator.validator"):
                    return True
                if n.name.startswith("strategy_validator.ledger.writer"):
                    return True
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "__import__":
                if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                    name = node.args[0].value
                    if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.ledger.writer"):
                        return True
            if isinstance(node.func, ast.Attribute):
                if (
                    isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "importlib"
                    and node.func.attr == "import_module"
                ):
                    if node.args and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                        name = node.args[0].value
                        if name.startswith("strategy_validator.validator") or name.startswith("strategy_validator.ledger.writer"):
                            return True
    return False


def test_api_mutation_detector_flags_validator_import(tmp_path: Path) -> None:
    sample = tmp_path / "api_mutation.py"
    sample.write_text("from strategy_validator.validator.orchestrator import adjudicate\n", encoding="utf-8")
    assert _api_module_violates_transport_thinness(sample) is True


def test_api_mutation_detector_flags_ledger_writer_import(tmp_path: Path) -> None:
    sample = tmp_path / "api_mutation_writer.py"
    sample.write_text("from strategy_validator.ledger.writer import commit_state_transition\n", encoding="utf-8")
    assert _api_module_violates_transport_thinness(sample) is True


def test_api_mutation_detector_flags_dynamic_import(tmp_path: Path) -> None:
    sample = tmp_path / "api_mutation_dynamic.py"
    sample.write_text("__import__('strategy_validator.validator.orchestrator')\n", encoding="utf-8")
    assert _api_module_violates_transport_thinness(sample) is True


def test_api_mutation_detector_flags_importlib_import_module(tmp_path: Path) -> None:
    sample = tmp_path / "api_mutation_importlib.py"
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
    assert _api_module_violates_transport_thinness(sample) is True


def test_api_mutation_detector_flags_dunder_import(tmp_path: Path) -> None:
    sample = tmp_path / "api_mutation_dunder.py"
    sample.write_text("__import__('strategy_validator.ledger.writer')\n", encoding="utf-8")
    assert _api_module_violates_transport_thinness(sample) is True
