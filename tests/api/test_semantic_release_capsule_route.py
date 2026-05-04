from __future__ import annotations

from pathlib import Path


def test_semantic_release_capsule_routes_are_registered() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")

    assert '@router.post("/semantic-adjudication-bundle/release-capsule")' in source
    assert '@router.post("/semantic-adjudication-bundle/release-capsule/verify")' in source
    assert "SemanticAdjudicationReleaseCapsuleRequest" in source
    assert "SemanticAdjudicationReleaseCapsuleVerificationRequest" in source
    assert "build_semantic_adjudication_release_capsule" in source
    assert "verify_semantic_adjudication_release_capsule" in source


def test_semantic_release_capsule_summary_route_is_registered() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")

    assert '@router.post("/semantic-adjudication-bundle/release-capsule/summary")' in source
    assert "summarize_semantic_adjudication_release_capsule" in source
    assert "semantic_adjudication_release_capsule_summary" not in source  # response comes from the application contract
