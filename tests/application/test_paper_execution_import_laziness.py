from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
HEAVY_IMPORTS = [
    "strategy_validator.contracts.paper_execution",
    "strategy_validator.contracts.paper_broker",
    "strategy_validator.application.paper_execution_evidence_bundle",
    "strategy_validator.application.paper_execution_evidence_bundle_verification",
    "strategy_validator.application.paper_execution_evidence_bundle_rotation",
    "strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation",
    "strategy_validator.brokers.alpaca_paper",
]


def _assert_import_adds_no_heavy_modules(module_name: str) -> None:
    """Assert importing a hotspot does not newly load the heavy paper execution graph.

    The test is intentionally transition-based so it remains stable when other
    tests in the same pytest process have already imported some contract modules.
    """

    before = {name: name in sys.modules for name in HEAVY_IMPORTS}
    importlib.import_module(module_name)
    after = {name: name in sys.modules for name in HEAVY_IMPORTS}
    newly_loaded = {name: after[name] for name in HEAVY_IMPORTS if not before[name] and after[name]}
    assert newly_loaded == {}


def _heavy_imports_in_source(path: Path) -> list[tuple[int, str]]:
    tree = ast.parse(path.read_text())
    findings: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.ImportFrom) or not node.module:
            continue
        if (
            node.module in {"strategy_validator.contracts.paper_execution", "strategy_validator.contracts.paper_broker"}
            or node.module.startswith("strategy_validator.brokers.")
            or node.module.startswith("strategy_validator.application.paper_execution_evidence_bundle")
        ):
            findings.append((node.lineno, node.module))
    return findings


def test_paper_execution_cockpit_import_does_not_load_heavy_contract_or_broker_graph() -> None:
    _assert_import_adds_no_heavy_modules("strategy_validator.application.paper_execution_cockpit")


def test_paper_broker_cli_import_does_not_load_heavy_contract_or_broker_graph() -> None:
    _assert_import_adds_no_heavy_modules("strategy_validator.cli.paper_broker")


def test_hotspot_modules_have_no_direct_heavy_imports() -> None:
    paths = [
        REPO_ROOT / "strategy_validator/application/paper_execution_cockpit.py",
        REPO_ROOT / "strategy_validator/cli/paper_broker.py",
    ]
    findings = {str(path.relative_to(REPO_ROOT)): _heavy_imports_in_source(path) for path in paths}
    assert findings == {str(path.relative_to(REPO_ROOT)): [] for path in paths}
