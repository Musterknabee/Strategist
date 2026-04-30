from __future__ import annotations

from strategy_validator.cli.migrate import run_migration
from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check


def test_migrated_ledger_path_satisfies_runtime_and_deployment_schema_readiness(tmp_path, monkeypatch) -> None:
    ledger_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    repo_root = tmp_path / "repo"
    repo_root.mkdir()

    monkeypatch.setenv("STRATEGY_VALIDATOR_MODE", "DEV")
    monkeypatch.setenv("STRATEGY_VALIDATOR_API_TOKEN", "readiness-secret")
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(ledger_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", str(backup_dir))

    migration = run_migration(database_path=str(ledger_path))
    assert migration["ok"] is True
    assert migration["schema_version_after"] == EXPECTED_SCHEMA_VERSION

    runtime = perform_readiness_check()
    assert runtime.schema_version == EXPECTED_SCHEMA_VERSION
    assert runtime.expected_schema_version == EXPECTED_SCHEMA_VERSION
    assert runtime.checks["schema_compatibility"] is True

    deployment = perform_deployment_readiness_check(repo_root=repo_root)
    assert deployment.status == "READY"
    assert deployment.checks["ledger_database_exists"] is True
    assert deployment.checks["ledger_backup_dir_writable"] is True
    assert deployment.checks["ledger_hash_chain_valid"] is True
    assert deployment.ledger_database_path == str(ledger_path)
