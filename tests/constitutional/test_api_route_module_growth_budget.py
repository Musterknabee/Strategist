from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ROUTES_DIR = ROOT / "strategy_validator" / "api" / "routes"


def test_api_route_module_count_is_budgeted() -> None:
    route_modules = sorted(path.name for path in ROUTES_DIR.glob("*.py") if path.name != "__init__.py")

    # This is a no-growth budget after the research-route split. New API modules
    # must justify an explicit architecture change rather than silently widening
    # the transport surface.
    assert len(route_modules) <= 15, route_modules


def test_research_router_remains_a_thin_composition_root() -> None:
    source = (ROUTES_DIR / "research.py").read_text(encoding="utf-8")

    assert "dependencies=[Depends(require_research_api_access)]" in source
    assert "router.include_router(bundle_router)" in source
    assert "router.include_router(release_router)" in source
    assert "router.include_router(handoff_router)" in source
    assert "router.include_router(validator_submission_router)" in source
    assert source.count("@router.post(") <= 6
