from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_public_facade import build_ui_public_facade_inventory
from strategy_validator.application.ui_research_os import build_ui_research_os_status_payload


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())


def test_research_os_payload_empty_degraded(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", str(tmp_path / "sb"))
    monkeypatch.setenv("STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT", str(tmp_path / "pt"))
    p = build_ui_research_os_status_payload(repo_root=tmp_path)
    assert p["schema_version"] == "ui_research_os_status/v1"
    assert "NO_BATCH_ARTIFACTS" in p["gauntlet_latest"]["degraded"]
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(p)


def test_research_os_route_returns_200(client: TestClient) -> None:
    r = client.get("/ui/research-os/status")
    assert r.status_code == 200
    body = r.json()
    assert body["schema_version"] == "ui_research_os_status/v1"
    assert "STRATEGY_VALIDATOR_API_TOKEN" not in str(body)


def test_ui_public_facade_lists_research_os_status(tmp_path: Path) -> None:
    inv = build_ui_public_facade_inventory(repo_root=tmp_path)
    routes = inv["routes"]
    match = [r for r in routes if r["path"] == "/ui/research-os/status" and r["method"] == "GET"]
    assert len(match) == 1
    assert match[0]["payload_schema"] == "ui_research_os_status/v1"
