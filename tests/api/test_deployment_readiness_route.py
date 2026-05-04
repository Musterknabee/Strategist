from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api.app import app


def test_deployment_readiness_route_uses_application_surface(monkeypatch) -> None:
    monkeypatch.setattr(
        "strategy_validator.api.routes.readiness.get_deployment_readiness_payload",
        lambda: {
            "ok": False,
            "surface": "deployment_readiness",
            "status": "BLOCKED",
            "runtime_readiness_status": "BLOCKED",
            "blocker_codes": ["PRIVATE_KEY_MATERIAL_IN_REPO"],
            "warning_codes": [],
            "checks": {"no_private_key_material_in_repo": False},
        },
    )
    client = TestClient(app)
    response = client.get("/readiness/deployment")
    assert response.status_code == 200
    payload = response.json()
    assert payload["surface"] == "deployment_readiness"
    assert payload["status"] == "BLOCKED"
    assert payload["blocker_codes"] == ["PRIVATE_KEY_MATERIAL_IN_REPO"]


def test_deployment_readiness_summary_route(monkeypatch) -> None:
    from strategy_validator.api.routes import readiness as readiness_routes

    monkeypatch.setattr(
        readiness_routes,
        "summarize_deployment_readiness_payload",
        lambda: {
            "schema_version": "deployment_readiness_summary/v1",
            "ok": True,
            "status": "READY",
            "recommended_action": "DEPLOYMENT_PREFLIGHT_READY",
            "runtime_readiness_status": "READY",
            "config_fingerprint": "abc123",
            "blocker_codes": [],
            "warning_codes": [],
            "failed_checks": [],
            "ledger_database_path": "/tmp/ledger.sqlite3",
            "ledger_backup_dir": "/tmp/backups",
        },
    )

    payload = readiness_routes.deployment_readiness_summary()

    assert payload["schema_version"] == "deployment_readiness_summary/v1"
    assert payload["recommended_action"] == "DEPLOYMENT_PREFLIGHT_READY"
