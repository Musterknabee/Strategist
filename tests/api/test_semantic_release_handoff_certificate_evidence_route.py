from __future__ import annotations

from pathlib import Path


def test_release_handoff_certificate_evidence_routes_are_declared() -> None:
    routes = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")

    assert "/semantic-adjudication-bundle/release-handoff-certificate/evidence" in routes
    assert "/semantic-adjudication-bundle/release-handoff-certificate/evidence/verify" in routes
    assert "build_semantic_release_handoff_certificate_evidence" in routes
    assert "verify_semantic_release_handoff_certificate_evidence" in routes
