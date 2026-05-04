from __future__ import annotations

from pathlib import Path

from strategy_validator.ledger._append_only import inspect_schema_version_info_readonly
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check


def test_readiness_schema_inspection_does_not_create_missing_ledger(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "missing" / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))

    current, expected = inspect_schema_version_info_readonly()
    runtime = perform_readiness_check()
    deployment = perform_deployment_readiness_check(repo_root=tmp_path)

    assert current == 0
    assert expected >= 1
    assert runtime.schema_version == 0
    assert deployment.checks["ledger_database_exists"] is False
    assert deployment.checks["ledger_hash_chain_valid"] is False
    assert not database_path.exists()
    assert not database_path.parent.exists()
