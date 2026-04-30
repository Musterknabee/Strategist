from __future__ import annotations

from pathlib import Path


def test_release_capsule_contracts_and_builders_are_declared() -> None:
    contracts = Path("strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    integrity = Path("strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticAdjudicationReleaseCapsule" in contracts
    assert "class SemanticAdjudicationReleaseCapsuleVerificationReport" in contracts
    assert "def build_semantic_adjudication_release_capsule" in integrity
    assert "def verify_semantic_adjudication_release_capsule" in integrity
    assert "SEMANTIC_RELEASE_CAPSULE_CHECKSUM_MISMATCH" in integrity
    assert "SEMANTIC_RELEASE_CAPSULE_INDEX_VERIFICATION_DRIFT" in integrity


def test_release_capsule_is_exported_from_application_facade() -> None:
    exports = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")
    root = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")

    assert "build_semantic_adjudication_release_capsule" in exports
    assert "verify_semantic_adjudication_release_capsule" in exports
    assert "build_semantic_adjudication_release_capsule" in root
    assert "verify_semantic_adjudication_release_capsule" in root


def test_release_capsule_summary_contract_and_builder_are_declared() -> None:
    contracts = Path("strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    integrity = Path("strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticAdjudicationReleaseCapsuleSummary" in contracts
    assert "semantic_adjudication_release_capsule_summary/v1" in contracts
    assert "def summarize_semantic_adjudication_release_capsule" in integrity
    assert "ACCEPT_SEMANTIC_RELEASE_CAPSULE_FOR_ADJUDICATION" in integrity
    assert "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_CAPSULE" in integrity


def test_release_capsule_summary_is_exported_from_application_facade() -> None:
    exports = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")
    root = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")

    assert "summarize_semantic_adjudication_release_capsule" in exports
    assert "summarize_semantic_adjudication_release_capsule" in root
