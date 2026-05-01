from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.api.probes import register_api_probes, register_api_root_banner


class _Readiness:
    def __init__(self, status: str) -> None:
        self.status = status

    def model_dump(self, *, mode: str = "json") -> dict[str, object]:
        return {"status": self.status, "checks": {}}


def test_readyz_returns_503_when_runtime_readiness_blocks(monkeypatch) -> None:
    monkeypatch.setattr("strategy_validator.api.probes.perform_readiness_check", lambda: _Readiness("BLOCKED"))
    app = register_api_probes(FastAPI())

    response = TestClient(app).get("/readyz")

    assert response.status_code == 503
    assert response.json()["ok"] is False
    assert response.json()["status"] == "BLOCKED"


def test_root_operator_banner_lists_probe_and_facade_links() -> None:
    app = create_app()
    response = TestClient(app).get("/")

    assert response.status_code == 200
    body = response.json()
    assert body["service"] == "strategy-validator-api"
    assert body["schema_version"] == "api_root_banner/v1"
    links = body["links"]
    assert links["healthz"] == "/healthz"
    assert links["livez"] == "/livez"
    assert links["readyz"] == "/readyz"
    assert links["ui_facade"] == "/ui/facade"
    assert links.get("docs") == "/docs"


def test_root_operator_banner_omits_docs_when_openapi_ui_disabled() -> None:
    app = FastAPI(docs_url=None)
    register_api_probes(app)
    register_api_root_banner(app)

    response = TestClient(app).get("/")

    assert response.status_code == 200
    assert "docs" not in response.json()["links"]


def test_readyz_returns_200_when_runtime_readiness_is_ready(monkeypatch) -> None:
    monkeypatch.setattr("strategy_validator.api.probes.perform_readiness_check", lambda: _Readiness("READY"))
    app = register_api_probes(FastAPI())

    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["status"] == "READY"
