from __future__ import annotations

import pytest
from fastapi.testclient import TestClient


def test_ui_read_plane_has_no_cors_headers_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("STRATEGY_VALIDATOR_UI_CORS_ORIGINS", raising=False)
    from strategy_validator.api.app import create_app

    app = create_app()
    client = TestClient(app)
    response = client.get("/ui/facade", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert "access-control-allow-origin" not in response.headers


def test_ui_read_plane_reflects_configured_cors_origin(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_UI_CORS_ORIGINS", "http://localhost:3000")
    from strategy_validator.api.app import create_app

    app = create_app()
    client = TestClient(app)
    response = client.get("/ui/facade", headers={"Origin": "http://localhost:3000"})
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_ui_cors_preflight_options(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_UI_CORS_ORIGINS", "http://127.0.0.1:3000")
    from strategy_validator.api.app import create_app

    app = create_app()
    client = TestClient(app)
    response = client.options(
        "/ui/workboard",
        headers={
            "Origin": "http://127.0.0.1:3000",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert response.status_code == 200
    assert response.headers.get("access-control-allow-origin") == "http://127.0.0.1:3000"
