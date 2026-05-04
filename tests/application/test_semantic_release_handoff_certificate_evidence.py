from __future__ import annotations

from pathlib import Path


def test_release_handoff_certificate_evidence_contracts_and_builders_are_declared() -> None:
    contracts = Path("strategy_validator/contracts/semantic.py").read_text(encoding="utf-8")
    integrity = Path("strategy_validator/application/research_integrity.py").read_text(encoding="utf-8")

    assert "class SemanticReleaseHandoffCertificateEvidenceIssue" in contracts
    assert "class SemanticReleaseHandoffCertificateEvidenceVerificationReport" in contracts
    assert "semantic_release_handoff_certificate_evidence/v1" in integrity
    assert "def build_semantic_release_handoff_certificate_evidence" in integrity
    assert "def verify_semantic_release_handoff_certificate_evidence" in integrity
    assert "ALLOW_VALIDATOR_SEMANTIC_HANDOFF" in integrity
    assert "SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CHECKSUM_MISMATCH" in integrity
    assert "SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_HANDOFF_NOT_ALLOWED" in integrity


def test_release_handoff_certificate_evidence_is_exported_from_application_facade() -> None:
    exports = Path("strategy_validator/application/_exports.py").read_text(encoding="utf-8")
    root = Path("strategy_validator/application/__init__.py").read_text(encoding="utf-8")

    assert "build_semantic_release_handoff_certificate_evidence" in exports
    assert "verify_semantic_release_handoff_certificate_evidence" in exports
    assert "build_semantic_release_handoff_certificate_evidence" in root
    assert "verify_semantic_release_handoff_certificate_evidence" in root
