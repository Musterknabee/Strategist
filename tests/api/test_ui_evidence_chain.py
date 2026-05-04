from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from strategy_validator.api.app import app
from strategy_validator.ledger.operator_actions import append_operator_action_event


def test_ui_evidence_chain_route_returns_readonly_projection(monkeypatch, tmp_path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    append_operator_action_event(
        action="claim-item",
        operator_id="ops",
        target={"work_item_key": "wk-route", "idempotency_key": "route-ev-chain"},
        summary_line="claimed route item",
        created_at_utc=datetime(2026, 5, 2, 11, 0, tzinfo=timezone.utc),
    )
    client = TestClient(app)

    response = client.get("/ui/evidence-chain?readonly=true")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_evidence_chain/v1"
    assert payload["read_plane_only"] is True
    assert payload["summary"]["operator_action_event_count"] == 1
    assert payload["streams"]["operator_action_journal"]["chain_ok"] is True
    assert payload["timeline"]["entries"][0]["stream_family"] == "operator_action_journal"


def test_ui_evidence_chain_is_declared_in_facade() -> None:
    client = TestClient(app)
    response = client.get("/ui/facade")
    assert response.status_code == 200
    routes = {(route["method"], route["path"], route["auth_required"]) for route in response.json()["routes"]}
    assert ("GET", "/ui/evidence-chain", False) in routes
