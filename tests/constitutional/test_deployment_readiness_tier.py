from __future__ import annotations

from pathlib import Path

from strategy_validator.cli.migrate import run_migration
from strategy_validator.validator.readiness import perform_deployment_readiness_check


def test_deployment_readiness_reports_backup_and_hash_chain_status(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    run_migration(database_path=str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", str(backup_dir))

    report = perform_deployment_readiness_check(repo_root=tmp_path)

    assert report.checks["ledger_database_exists"] is True
    assert report.checks["ledger_backup_dir_configured"] is True
    assert report.checks["ledger_backup_dir_writable"] is True
    assert report.checks["ledger_hash_chain_valid"] is True
    assert report.private_key_file_count == 0


def test_deployment_readiness_blocks_private_key_material(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    run_migration(database_path=str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", str(backup_dir))
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "bad.pem").write_text("-----BEGIN PRIVATE KEY-----\nsecret\n-----END PRIVATE KEY-----\n")

    report = perform_deployment_readiness_check(repo_root=tmp_path)

    assert report.status == "BLOCKED"
    assert report.private_key_file_count == 1
    assert "PRIVATE_KEY_MATERIAL_IN_REPO" in {blocker.code for blocker in report.blockers}
