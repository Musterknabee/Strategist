from __future__ import annotations

from fastapi.routing import APIRoute

from strategy_validator.api.app import app


def test_api_routes_present() -> None:
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert '/adjudication/health' in paths
    assert '/queue/health' in paths
    assert '/rebuild/projection-health' in paths
    assert '/readiness/health' in paths
