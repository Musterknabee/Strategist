import ast
from pathlib import Path


def _contains_forbidden_adjudicate_call(path: Path) -> bool:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "adjudicate":
                return True
            if isinstance(node.func, ast.Attribute) and node.func.attr == "adjudicate":
                return True
    return False


def test_api_has_no_direct_adjudicate_calls() -> None:
    api_root = Path(__file__).resolve().parents[2] / "strategy_validator" / "api"
    for path in api_root.rglob("*.py"):
        if "__pycache__" in path.parts:
            continue
        assert _contains_forbidden_adjudicate_call(path) is False, (
            f"Constitutional violation: api transport layer contains adjudicate() call in {path}"
        )


def test_api_mutation_detector_flags_adjudicate_call(tmp_path: Path) -> None:
    sample = tmp_path / "api_rogue_call.py"
    sample.write_text(
        "\n".join(
            [
                "def route(x):",
                "    return adjudicate(x, [])",
                "",
            ]
        ),
        encoding="utf-8",
    )
    assert _contains_forbidden_adjudicate_call(sample) is True
