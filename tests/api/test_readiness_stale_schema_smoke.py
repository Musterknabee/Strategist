from __future__ import annotations

from fastapi.testclient import TestClient

from strategy_validator.api import probes as probes_module
from strategy_validator.api.app import app
from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION
from strategy_validator.validator import readiness as readiness_module


def test_readyz_fails_when_schema_version_is_stale(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(tmp_path / "ledger.sqlite3"))
    monkeypatch.setattr(
        readiness_module,
        "get_schema_version_info",
        lambda: (EXPECTED_SCHEMA_VERSION - 1, EXPECTED_SCHEMA_VERSION),
    )
    monkeypatch.setattr(probes_module, "perform_readiness_check", readiness_module.perform_readiness_check)

    response = TestClient(app).get("/readyz")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "BLOCKED"
    assert payload["schema_version"] == EXPECTED_SCHEMA_VERSION - 1
    assert payload["expected_schema_version"] == EXPECTED_SCHEMA_VERSION
    assert any(item["code"] == "INCOMPATIBLE_SCHEMA" for item in payload["blockers"])
