from __future__ import annotations

from pathlib import Path


def test_semantic_release_handoff_certificate_evidence_summary_route_is_registered() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")
    assert "/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary" in source
    assert "summarize_semantic_release_handoff_certificate_evidence" in source
