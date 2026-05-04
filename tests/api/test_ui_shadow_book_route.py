from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory


def test_shadow_book_route_returns_200() -> None:
    client = TestClient(create_app())
    r = client.get("/ui/shadow-book/latest")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "ui_shadow_book/v1"
    assert body["read_plane_only"] is True
    assert body["no_order_controls"] is True
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(body)


def test_ui_public_facade_lists_shadow_book() -> None:
    inv = build_ui_public_facade_inventory()
    assert any(r["method"] == "GET" and r["path"] == "/ui/shadow-book/latest" for r in inv["routes"])
