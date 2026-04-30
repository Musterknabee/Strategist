from __future__ import annotations

from pathlib import Path


def test_semantic_release_index_routes_are_registered() -> None:
    source = Path("strategy_validator/api/routes/research_release.py").read_text(encoding="utf-8")

    assert '@router.post("/semantic-adjudication-bundle/release-index")' in source
    assert '@router.post("/semantic-adjudication-bundle/release-index/verify")' in source
    assert '@router.post("/semantic-adjudication-bundle/release-preflight")' in source
    assert "SemanticAdjudicationBundleReleaseIndexRequest" in source
    assert "SemanticAdjudicationBundleReleaseIndexVerificationRequest" in source
