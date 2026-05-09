from __future__ import annotations

from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory
from strategy_validator.application.ui_views import build_ui_tribunal_payload


def test_ui_tribunal_facade_schema_matches_payload() -> None:
    facade = build_ui_public_facade_inventory()
    route = next(route for route in facade['routes'] if route['method'] == 'GET' and route['path'] == '/ui/tribunal')
    payload = build_ui_tribunal_payload()

    assert route['payload_schema'] == payload['schema_version']
    assert route['auth_required'] is False
    assert route['kind'] == 'read'
