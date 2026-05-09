from __future__ import annotations

import ast
import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPLICATION = ROOT / "strategy_validator" / "application"

SUBPHASE_MODULES = (
    "research_integrity_validator_submission_acceptance_record",
    "research_integrity_validator_submission_acceptance_ledger",
    "research_integrity_validator_submission_packet",
    "research_integrity_validator_submission_evidence",
    "research_integrity_validator_submission_readiness",
)


def _function_names(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {node.name for node in tree.body if isinstance(node, ast.FunctionDef)}


def test_validator_submission_public_module_is_thin_facade() -> None:
    facade_path = APPLICATION / "research_integrity_validator_submission.py"
    source = facade_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 60
    assert _function_names(facade_path) == set()
    assert "SemanticValidatorSubmissionPacket(" not in source
    assert "SemanticValidatorIngressAcceptanceLedger(" not in source


def test_validator_submission_subphases_own_expected_responsibilities() -> None:
    expected = {
        "research_integrity_validator_submission_acceptance_record": {
            "build_semantic_validator_ingress_acceptance_record",
            "verify_semantic_validator_ingress_acceptance_record",
            "summarize_semantic_validator_ingress_acceptance_record",
        },
        "research_integrity_validator_submission_acceptance_ledger": {
            "build_semantic_validator_ingress_acceptance_ledger",
            "verify_semantic_validator_ingress_acceptance_ledger",
            "summarize_semantic_validator_ingress_acceptance_ledger",
        },
        "research_integrity_validator_submission_packet": {
            "build_semantic_validator_submission_packet",
            "verify_semantic_validator_submission_packet",
            "summarize_semantic_validator_submission_packet",
        },
        "research_integrity_validator_submission_evidence": {
            "build_semantic_validator_submission_packet_evidence",
            "verify_semantic_validator_submission_packet_evidence",
            "summarize_semantic_validator_submission_packet_evidence",
        },
        "research_integrity_validator_submission_readiness": {
            "build_semantic_validator_submission_readiness_report",
            "summarize_semantic_validator_submission_readiness",
        },
    }

    for module_name, function_names in expected.items():
        assert function_names <= _function_names(APPLICATION / f"{module_name}.py")


def test_validator_submission_facade_exports_match_subphases() -> None:
    facade = importlib.import_module("strategy_validator.application.research_integrity_validator_submission")
    expected_exports: list[str] = []
    for module_name in SUBPHASE_MODULES:
        module = importlib.import_module(f"strategy_validator.application.{module_name}")
        expected_exports.extend(module.__all__)

    assert list(facade.__all__) == expected_exports


def test_validator_submission_legacy_import_surface_is_preserved() -> None:
    from strategy_validator.application.research_integrity_validator_submission import (  # noqa: PLC0415
        build_semantic_validator_ingress_acceptance_ledger,
        build_semantic_validator_ingress_acceptance_record,
        build_semantic_validator_submission_packet,
        build_semantic_validator_submission_packet_evidence,
        build_semantic_validator_submission_readiness_report,
        summarize_semantic_validator_submission_packet,
        verify_semantic_validator_submission_packet,
    )

    assert callable(build_semantic_validator_ingress_acceptance_record)
    assert callable(build_semantic_validator_ingress_acceptance_ledger)
    assert callable(build_semantic_validator_submission_packet)
    assert callable(verify_semantic_validator_submission_packet)
    assert callable(summarize_semantic_validator_submission_packet)
    assert callable(build_semantic_validator_submission_packet_evidence)
    assert callable(build_semantic_validator_submission_readiness_report)
