from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_research_compute_route_returns_readonly_payload() -> None:
    client = TestClient(app)
    response = client.get("/ui/research-compute")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("schema_version") == "ui_research_compute/v1"
    assert payload.get("read_plane_only") is True
    assert payload.get("advisory_only") is True
    assert isinstance(payload.get("gpu_probe"), dict)
