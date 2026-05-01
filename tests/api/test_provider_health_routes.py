from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_readiness_provider_health_route_returns_snapshot() -> None:
    client = TestClient(app)
    response = client.get("/readiness/provider-health")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("schema_version") == "provider_health_snapshot/v1"
    assert "entries" in payload
    assert "apikey=" not in response.text.lower()
    assert "sk-" not in response.text


def test_ui_provider_health_route_matches_read_plane() -> None:
    client = TestClient(app)
    r1 = client.get("/readiness/provider-health")
    r2 = client.get("/ui/provider-health")
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["schema_version"] == r2.json()["schema_version"]
    assert len(r1.json()["entries"]) == len(r2.json()["entries"])
