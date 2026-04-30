from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient

from strategy_validator.api.probes import register_api_probes


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


def test_readyz_returns_200_when_runtime_readiness_is_ready(monkeypatch) -> None:
    monkeypatch.setattr("strategy_validator.api.probes.perform_readiness_check", lambda: _Readiness("READY"))
    app = register_api_probes(FastAPI())

    response = TestClient(app).get("/readyz")

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["status"] == "READY"
