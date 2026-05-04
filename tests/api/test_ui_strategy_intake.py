from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_ui_strategy_intake_route_records_artifact(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.delenv("STRATEGY_VALIDATOR_API_TOKEN", raising=False)
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(tmp_path / "artifacts"))
    client = TestClient(app)

    response = client.post(
        "/ui/strategy-intake",
        json={
            "strategy_name": "Liquidity Sweep Reversal",
            "thesis": "Detect exhaustion after liquidity sweep and require PIT-safe confirmation.",
            "target_universe": "crypto majors",
            "intended_horizon": "intraday",
            "expected_edge": "Stop-run reversal with bounded holding time.",
            "data_dependencies": ["orderbook_snapshot", "trades"],
            "falsification_rules": ["kill after three unrecovered sweep failures"],
            "risk_assumptions": ["no leverage escalation"],
            "operator_id": "jp",
            "idempotency_key": "ui-intake-route-1",
        },
        headers={"x-strategy-validator-operator": "jp"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["accepted"] is True
    assert payload["authority_boundary"] == "ADVISORY_ARTIFACT_ONLY"
    assert payload["promotion_authority"] == "NONE"
    assert Path(payload["artifact_path"]).is_file()

    latest = client.get("/ui/strategy-intake/latest")
    assert latest.status_code == 200
    latest_payload = latest.json()
    assert latest_payload["schema_version"] == "ui_strategy_intake/v1"
    assert latest_payload["latest"]["intake_count"] == 1
    assert latest_payload["latest"]["entries"][0]["proposal_id"] == payload["proposal_id"]


def test_ui_strategy_intake_is_declared_in_facade() -> None:
    client = TestClient(app)
    response = client.get("/ui/facade")
    assert response.status_code == 200
    routes = {(route["method"], route["path"], route["auth_required"]) for route in response.json()["routes"]}
    assert ("GET", "/ui/strategy-intake/latest", False) in routes
    assert ("POST", "/ui/strategy-intake", True) in routes
