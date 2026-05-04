from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory


def test_strategy_memory_route_returns_200() -> None:
    client = TestClient(create_app())
    r = client.get("/ui/strategy-memory/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "ui_strategy_memory/v1"
    assert body["read_plane_only"] is True
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(body)


def test_ui_public_facade_lists_strategy_memory() -> None:
    inv = build_ui_public_facade_inventory()
    routes = inv["routes"]
    assert any(r["method"] == "GET" and r["path"] == "/ui/strategy-memory/latest" for r in routes)
