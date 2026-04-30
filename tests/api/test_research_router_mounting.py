from __future__ import annotations

from strategy_validator.api.app import app
from strategy_validator.api.route_registry import iter_api_routers
from strategy_validator.api.routes.research import router as research_router


def _paths() -> set[str]:
    return {getattr(route, "path", "") for route in app.routes}


def test_research_router_is_registered_once_by_route_registry() -> None:
    routers = tuple(iter_api_routers())

    assert research_router in routers
    assert routers.count(research_router) == 1


def test_extracted_research_routes_are_mounted_under_research_prefix() -> None:
    paths = _paths()

    expected = {
        "/research/semantic-preflight",
        "/research/semantic-adjudication-readiness",
        "/research/semantic-adjudication-handoff/artifact",
        "/research/semantic-adjudication-bundle",
        "/research/semantic-adjudication-bundle/release-preflight",
        "/research/semantic-adjudication-bundle/validator-handoff-packet",
        "/research/semantic-adjudication-bundle/validator-submission-packet",
    }

    assert expected <= paths
