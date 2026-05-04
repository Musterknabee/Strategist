from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.routing import APIRoute

from strategy_validator.api.probes import PROBE_ROUTES, register_api_probes


def test_api_app_uses_probe_registry() -> None:
    app_text = Path('strategy_validator/api/app.py').read_text(encoding='utf-8')

    assert 'from strategy_validator.api.probes import register_api_probes, register_api_root_banner' in app_text
    assert 'register_api_probes(app)' in app_text
    assert 'register_api_root_banner(app)' in app_text
    assert "@app.get('/healthz')" not in app_text
    assert "@app.get('/livez')" not in app_text
    assert "@app.get('/readyz')" not in app_text
    assert "@app.get('/')" not in app_text


def test_api_probe_registry_registers_expected_paths() -> None:
    app = FastAPI()
    register_api_probes(app)
    paths = {route.path for route in app.routes if isinstance(route, APIRoute)}
    assert '/healthz' in paths
    assert '/livez' in paths
    assert '/readyz' in paths


def test_probe_routes_surface_is_stable() -> None:
    assert PROBE_ROUTES == (
        ('/healthz', PROBE_ROUTES[0][1]),
        ('/livez', PROBE_ROUTES[1][1]),
        ('/readyz', PROBE_ROUTES[2][1]),
    )
    assert [path for path, _ in PROBE_ROUTES] == ['/healthz', '/livez', '/readyz']


def test_probe_registry_lazily_imports_runtime_readiness() -> None:
    content = Path('strategy_validator/api/probes.py').read_text(encoding='utf-8')

    before_function = content.split('def perform_readiness_check', 1)[0]
    assert 'strategy_validator.application.readiness' not in before_function
    assert 'get_runtime_readiness_report' in content
