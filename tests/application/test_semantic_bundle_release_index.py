from __future__ import annotations

from pathlib import Path


def test_release_index_contracts_and_builders_are_declared() -> None:
    contracts = Path("strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    integrity = Path("strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticAdjudicationBundleReleaseIndex" in contracts
    assert "class SemanticAdjudicationBundleReleaseIndexVerificationReport" in contracts
    assert "def build_semantic_adjudication_bundle_release_index" in integrity
    assert "def verify_semantic_adjudication_bundle_release_index" in integrity
    assert "SEMANTIC_RELEASE_INDEX_CHECKSUM_MISMATCH" in integrity
    assert "SEMANTIC_RELEASE_INDEX_PREFLIGHT_DRIFT" in integrity


def test_release_index_is_exported_from_application_facade() -> None:
    exports = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")
    root = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")

    assert "build_semantic_adjudication_bundle_release_index" in exports
    assert "verify_semantic_adjudication_bundle_release_index" in exports
    assert "build_semantic_adjudication_bundle_release_index" in root
    assert "verify_semantic_adjudication_bundle_release_index" in root
