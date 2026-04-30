from __future__ import annotations

from pathlib import Path


def test_research_route_has_no_growth_budget_and_http_guard() -> None:
    source_path = Path("strategy_validator/api/routes/research.py")
    source = source_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 260
    assert "require_research_api_access" in source
    assert "dependencies=[Depends(require_research_api_access)]" in source
    assert "router.include_router(bundle_router)" in source
    assert "router.include_router(release_router)" in source
    assert "router.include_router(handoff_router)" in source
    assert "router.include_router(validator_submission_router)" in source


def test_research_release_route_has_bounded_release_surface() -> None:
    source_path = Path("strategy_validator/api/routes/research_release.py")
    source = source_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 560
    assert "APIRouter" in source
    assert "/release-decision-record" in source
    assert "/release-decision-ledger" in source
    assert "/release-handoff-certificate" in source


def test_research_handoff_route_has_bounded_terminal_ingress_surface() -> None:
    source_path = Path("strategy_validator/api/routes/research_handoff.py")
    source = source_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 330
    assert "APIRouter" in source
    assert "/validator-handoff-packet" in source
    assert "/ingress/acceptance-record" in source
    assert "/ingress/acceptance-ledger" in source


def test_research_submission_route_has_bounded_terminal_handoff_surface() -> None:
    source_path = Path("strategy_validator/api/routes/research_submission.py")
    source = source_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 220
    assert "APIRouter" in source
    assert "/validator-submission-packet" in source
    assert "/validator-submission/readiness" in source


def test_research_bundle_route_has_bounded_bundle_surface() -> None:
    source_path = Path("strategy_validator/api/routes/research_bundle.py")
    source = source_path.read_text(encoding="utf-8")

    assert len(source.splitlines()) <= 170
    assert "APIRouter" in source
    assert "/semantic-adjudication-readiness" in source
    assert "/semantic-adjudication-bundle" in source
    assert "/semantic-adjudication-handoff/artifact" in source
