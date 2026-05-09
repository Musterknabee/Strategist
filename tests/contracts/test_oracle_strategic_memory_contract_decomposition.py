from __future__ import annotations

import ast
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
CONTRACTS = ROOT / "strategy_validator" / "contracts"

SUBPHASE_MODULES = (
    "oracle_strategic_memory_common",
    "oracle_strategic_memory_thesis",
    "oracle_strategic_memory_doctrine",
    "oracle_strategic_memory_research",
    "oracle_strategic_memory_graph",
    "oracle_strategic_memory_tension_narrative",
    "oracle_strategic_memory_horizon",
    "oracle_strategic_memory_resolution_intervention",
)


def _class_names(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.ClassDef)]


def test_oracle_strategic_memory_is_legacy_facade() -> None:
    facade_path = CONTRACTS / "oracle_strategic_memory.py"

    assert len(facade_path.read_text(encoding="utf-8").splitlines()) <= 40
    assert _class_names(facade_path) == []


def test_oracle_strategic_memory_subphases_own_expected_contract_families() -> None:
    expected_classes = {
        "oracle_strategic_memory_thesis": {
            "OracleThesisMemoryItem",
            "OracleThesisMemoryReport",
        },
        "oracle_strategic_memory_doctrine": {
            "OracleDoctrineAdaptationItem",
            "OracleDoctrineAdaptationReport",
        },
        "oracle_strategic_memory_research": {
            "OracleResearchPriorityItem",
            "OracleResearchPriorityReport",
            "OracleInvestigationOutcomeInput",
            "OracleResearchExecutionMemoryReport",
        },
        "oracle_strategic_memory_graph": {
            "OracleThesisGraphNode",
            "OracleThesisGraphEdge",
            "OracleThesisGraphReport",
        },
        "oracle_strategic_memory_tension_narrative": {
            "OracleStrategicTensionItem",
            "OracleStrategicTensionReport",
            "OracleStrategicNarrativeItem",
            "OracleStrategicNarrativeReport",
        },
        "oracle_strategic_memory_horizon": {
            "OracleStrategicMemoryPoint",
            "OracleStrategicDriverDriftItem",
            "OracleStrategicMemoryHorizonReport",
        },
        "oracle_strategic_memory_resolution_intervention": {
            "OracleContradictionResolutionItem",
            "OracleContradictionResolutionReport",
            "OracleStrategicInterventionItem",
            "OracleStrategicInterventionReport",
        },
    }

    for module_name, class_names in expected_classes.items():
        owned = set(_class_names(CONTRACTS / f"{module_name}.py"))
        assert class_names <= owned


def test_oracle_strategic_memory_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.contracts.oracle_strategic_memory")
    expected_exports: list[str] = []
    for subphase_name in SUBPHASE_MODULES:
        subphase = importlib.import_module(f"strategy_validator.contracts.{subphase_name}")
        expected_exports.extend(subphase.__all__)

    assert list(facade.__all__) == expected_exports


def test_legacy_oracle_strategic_memory_import_surface_stays_available() -> None:
    facade = importlib.import_module("strategy_validator.contracts.oracle_strategic_memory")

    assert facade.OracleStrategicPosture is not None
    assert facade.OracleThesisMemoryReport.__name__ == "OracleThesisMemoryReport"
    assert facade.OracleDoctrineAdaptationReport.__name__ == "OracleDoctrineAdaptationReport"
    assert facade.OracleResearchPriorityReport.__name__ == "OracleResearchPriorityReport"
    assert facade.OracleThesisGraphReport.__name__ == "OracleThesisGraphReport"
    assert facade.OracleStrategicNarrativeReport.__name__ == "OracleStrategicNarrativeReport"
    assert facade.OracleStrategicMemoryHorizonReport.__name__ == "OracleStrategicMemoryHorizonReport"
    assert facade.OracleStrategicInterventionReport.__name__ == "OracleStrategicInterventionReport"
