from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

from strategy_validator.api.route_registry import iter_api_routers, register_api_routes



def test_api_app_uses_bounded_route_registry() -> None:
    app_text = Path('strategy_validator/api/app.py').read_text(encoding='utf-8')

    assert 'from strategy_validator.api.route_registry import register_api_routes' in app_text
    assert 'register_api_routes(app)' in app_text
    assert 'app.include_router(adjudication_router)' not in app_text
    assert 'app.include_router(queue_router)' not in app_text
    assert 'app.include_router(rebuild_router)' not in app_text
    assert 'app.include_router(readiness_router)' not in app_text
    assert 'app.include_router(ui_router)' not in app_text



def test_api_route_registry_owns_router_registration_order() -> None:
    registry_text = Path('strategy_validator/api/route_registry.py').read_text(encoding='utf-8')

    assert 'from strategy_validator.api.routes.adjudication import router as adjudication_router' in registry_text
    assert 'from strategy_validator.api.routes.queue import router as queue_router' in registry_text
    assert 'from strategy_validator.api.routes.rebuild import router as rebuild_router' in registry_text
    assert 'from strategy_validator.api.routes.readiness import router as readiness_router' in registry_text
    assert 'from strategy_validator.api.routes.ui import router as ui_router' in registry_text
    assert '_API_ROUTERS: tuple[APIRouter, ...] = (' in registry_text
    assert 'def register_api_routes(app: FastAPI) -> FastAPI:' in registry_text



def test_route_registry_registers_expected_paths() -> None:
    app = FastAPI()
    register_api_routes(app)
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert '/adjudication/health' in paths
    assert '/queue/health' in paths
    assert '/rebuild/projection-health' in paths
    assert '/readiness/health' in paths
    assert '/ui/workboard' in paths



def test_iter_api_routers_is_stable_tuple_surface() -> None:
    routers = tuple(iter_api_routers())
    assert len(routers) == 5
    assert all(hasattr(router, 'routes') for router in routers)
