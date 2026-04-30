import ast
import os
from pathlib import Path
from typing import Set

REPO_ROOT = Path(__file__).resolve().parents[2]
PKG_ROOT = REPO_ROOT / "strategy_validator"


def _py_files(base: Path) -> list[Path]:
    out: list[Path] = []
    for dirpath, dirnames, filenames in os.walk(base):
        if "__pycache__" in dirnames:
            dirnames.remove("__pycache__")
        for f in filenames:
            if f.endswith(".py"):
                out.append(Path(dirpath) / f)
    return out


def get_imports(file_path: Path) -> Set[str]:
    with open(file_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(file_path))

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                imports.add(n.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imports.add(node.module)
    return imports


def _paths_with_forbidden_writer_imports(base: Path) -> list[Path]:
    violating_paths: list[Path] = []
    writer_root = PKG_ROOT / "ledger" / "writer"
    orch_root = PKG_ROOT / "validator" / "orchestrator"

    for path in _py_files(base):
        if writer_root in path.parents or orch_root in path.parents:
            continue
        imports = get_imports(path)
        for imp in imports:
            if imp == "strategy_validator.ledger.writer" or imp.startswith(
                "strategy_validator.ledger.writer."
            ):
                violating_paths.append(path)
                break
    return violating_paths


def test_proposers_boundaries() -> None:
    """proposers/ may import only core, contracts, api, and intra-proposers."""
    proposers_path = PKG_ROOT / "proposers"
    allowed_prefixes = (
        "strategy_validator.core",
        "strategy_validator.contracts",
        "strategy_validator.api",
        "strategy_validator.proposers",
    )
    allowed_exact = {"typing", "datetime", "pydantic", "__future__", "dataclasses", "enum"}

    for path in _py_files(proposers_path):
        imports = get_imports(path)
        for imp in imports:
            if imp in allowed_exact:
                continue
            if imp.startswith("strategy_validator"):
                if not any(imp == p or imp.startswith(p + ".") for p in allowed_prefixes):
                    raise AssertionError(
                        f"Constitutional violation: {path} imports forbidden module {imp}"
                    )


def test_tribunal_boundaries() -> None:
    """tribunal/ may not import validator/, ledger.writer, or feature_factory."""
    tribunal_path = PKG_ROOT / "tribunal"
    forbidden_prefixes = (
        "strategy_validator.validator",
        "strategy_validator.ledger.writer",
        "strategy_validator.feature_factory",
    )

    for path in _py_files(tribunal_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == fp or imp.startswith(fp + ".") for fp in forbidden_prefixes):
                raise AssertionError(
                    f"Constitutional violation: {path} imports forbidden module {imp}"
                )


def test_ledger_writer_restriction() -> None:
    """Only validator.orchestrator may import ledger.writer."""
    violating_paths = _paths_with_forbidden_writer_imports(PKG_ROOT)
    if violating_paths:
        joined = ", ".join(str(path) for path in violating_paths)
        raise AssertionError(
            f"Constitutional violation: ledger.writer imported outside orchestrator in {joined}"
        )


def test_ledger_writer_restriction_detector_flags_direct_imports(tmp_path: Path) -> None:
    sample = tmp_path / "rogue_module.py"
    sample.write_text(
        "from strategy_validator.ledger.writer import commit_state_transition\n",
        encoding="utf-8",
    )
    violating_paths = _paths_with_forbidden_writer_imports(tmp_path)
    assert violating_paths == [sample]


def test_feature_factory_boundaries() -> None:
    """feature_factory/ may not import validator or tribunal."""
    ff_path = PKG_ROOT / "feature_factory"
    forbidden_prefixes = ("strategy_validator.validator", "strategy_validator.tribunal")

    for path in _py_files(ff_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == fp or imp.startswith(fp + ".") for fp in forbidden_prefixes):
                raise AssertionError(
                    f"Constitutional violation: {path} imports forbidden module {imp}"
                )


def test_api_remains_transport_thin() -> None:
    api_path = PKG_ROOT / "api"
    forbidden_prefixes = ("strategy_validator.validator", "strategy_validator.ledger.writer")
    for path in _py_files(api_path):
        imports = get_imports(path)
        for imp in imports:
            if any(imp == fp or imp.startswith(fp + ".") for fp in forbidden_prefixes):
                raise AssertionError(
                    f"Constitutional violation: {path} imports forbidden module {imp}"
                )
