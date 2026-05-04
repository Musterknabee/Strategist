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


def test_deployment_readiness_rejects_symlinked_backup_root(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    run_migration(database_path=str(database_path))
    real_backup_dir = tmp_path / "real-backups"
    real_backup_dir.mkdir()
    symlinked_backup_dir = tmp_path / "backup-link"
    symlinked_backup_dir.symlink_to(real_backup_dir, target_is_directory=True)

    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", str(symlinked_backup_dir))

    report = perform_deployment_readiness_check(repo_root=tmp_path)

    assert report.status == "BLOCKED"
    assert report.checks["backup_root_path_integrity"] is False
    assert report.checks["backup_root_writable"] is False
    assert "BACKUP_ROOT_IS_SYMLINK" in {blocker.code for blocker in report.blockers}


def test_deployment_readiness_rejects_artifact_root_under_symlinked_parent(tmp_path: Path, monkeypatch) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    run_migration(database_path=str(database_path))
    real_parent = tmp_path / "real-artifact-parent"
    real_parent.mkdir()
    symlinked_parent = tmp_path / "artifact-parent-link"
    symlinked_parent.symlink_to(real_parent, target_is_directory=True)
    artifact_root = symlinked_parent / "artifacts"

    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", str(backup_dir))
    monkeypatch.setenv("STRATEGY_VALIDATOR_ARTIFACT_ROOT", str(artifact_root))

    report = perform_deployment_readiness_check(repo_root=tmp_path)

    assert report.status == "BLOCKED"
    assert report.checks["artifact_root_path_integrity"] is False
    assert report.checks["artifact_root_writable"] is False
    assert "ARTIFACT_ROOT_PARENT_IS_SYMLINK" in {blocker.code for blocker in report.blockers}
