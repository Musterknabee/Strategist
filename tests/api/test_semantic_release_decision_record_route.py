from __future__ import annotations

from pathlib import Path


def test_release_decision_record_routes_are_declared() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")

    assert "/semantic-adjudication-bundle/release-decision-record" in source
    assert "/semantic-adjudication-bundle/release-decision-record/verify" in source
    assert "/semantic-adjudication-bundle/release-decision-record/summary" in source
    assert "SemanticAdjudicationReleaseDecisionRecordRequest" in source
    assert "SemanticAdjudicationReleaseDecisionRecordVerificationRequest" in source
    assert "build_semantic_adjudication_release_decision_record" in source
    assert "verify_semantic_adjudication_release_decision_record" in source
    assert "summarize_semantic_adjudication_release_decision_record" in source
