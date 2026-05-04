from __future__ import annotations

import json
from pathlib import Path

import pytest

from strategy_validator.cli.ledger_ops import (
    LedgerOpsError,
    backup_ledger_database,
    main,
    restore_ledger_database,
    verify_ledger,
    verify_ledger_integrity,
)
from strategy_validator.cli.migrate import run_migration


def test_ledger_ops_verify_reports_schema_and_hash_chain(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    run_migration(database_path=str(database_path))

    payload = verify_ledger(database_path=str(database_path))

    assert payload["ok"] is True
    assert payload["database_exists"] is True
    assert payload["hash_chain"]["ok"] is True


def test_ledger_ops_backup_creates_verified_copy(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    run_migration(database_path=str(database_path))

    payload = backup_ledger_database(database_path=str(database_path), backup_dir=str(backup_dir))

    assert payload["ok"] is True
    assert Path(payload["backup_path"]).exists()
    assert payload["post_backup_verification"]["ok"] is True
    assert payload["backup_sha256"]



def test_ledger_ops_verify_integrity_reports_single_json_payload(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    run_migration(database_path=str(database_path))

    payload = verify_ledger_integrity(database_path=str(database_path))

    assert payload["schema_version"] == "ledger_ops_integrity_verify/v1"
    assert payload["ok"] is True
    assert payload["database_sha256"]
    assert payload["ledger"]["schema_version"] == "ledger_ops_verify/v1"
    assert payload["operator_actions"]["schema_version"] == "ledger_ops_operator_action_chain_verify/v1"


def test_ledger_ops_cli_verify_integrity_json(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    run_migration(database_path=str(database_path))

    rc = main(["verify-integrity", "--database-path", str(database_path), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "ledger_ops_integrity_verify/v1"
    assert payload["ok"] is True


def test_ledger_ops_cli_verify_json(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    run_migration(database_path=str(database_path))

    rc = main(["verify", "--database-path", str(database_path), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "ledger_ops_verify/v1"
    assert payload["ok"] is True


def test_ledger_ops_restore_creates_verified_destination(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    restore_path = tmp_path / "restored" / "ledger.sqlite3"
    run_migration(database_path=str(database_path))
    backup = backup_ledger_database(database_path=str(database_path), backup_dir=str(backup_dir))

    payload = restore_ledger_database(
        backup_path=backup["backup_path"],
        database_path=str(restore_path),
    )

    assert payload["schema_version"] == "ledger_ops_restore/v1"
    assert payload["ok"] is True
    assert restore_path.exists()
    assert payload["post_restore_verification"]["ok"] is True




def test_ledger_ops_restore_preserves_displaced_destination_before_overwrite(tmp_path: Path) -> None:
    source_database_path = tmp_path / "source-ledger.sqlite3"
    destination_database_path = tmp_path / "destination-ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    pre_restore_dir = tmp_path / "pre-restore"
    run_migration(database_path=str(source_database_path))
    run_migration(database_path=str(destination_database_path))
    backup = backup_ledger_database(database_path=str(source_database_path), backup_dir=str(backup_dir))

    payload = restore_ledger_database(
        backup_path=backup["backup_path"],
        database_path=str(destination_database_path),
        allow_overwrite=True,
        pre_restore_backup_dir=str(pre_restore_dir),
    )

    assert payload["schema_version"] == "ledger_ops_restore/v1"
    assert payload["ok"] is True
    assert payload["restored_sha256"]
    assert payload["pre_restore_backup"]["schema_version"] == "ledger_ops_pre_restore_backup/v1"
    assert payload["pre_restore_backup"]["ok"] is True
    assert payload["pre_restore_backup"]["sha256"]
    assert Path(payload["pre_restore_backup"]["path"]).exists()
    assert Path(payload["pre_restore_backup"]["path"]).parent == pre_restore_dir


def test_ledger_ops_restore_refuses_existing_destination_without_override(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    restore_path = tmp_path / "restored.sqlite3"
    run_migration(database_path=str(database_path))
    run_migration(database_path=str(restore_path))
    backup = backup_ledger_database(database_path=str(database_path), backup_dir=str(backup_dir))

    rc = main([
        "restore",
        "--backup-path",
        backup["backup_path"],
        "--database-path",
        str(restore_path),
        "--json",
    ])

    assert rc == 2

from strategy_validator.cli.ledger_ops import verify_operator_action_journal
from strategy_validator.ledger.operator_actions import append_operator_action_event


def test_ledger_ops_verify_operator_actions_reports_chain(monkeypatch, tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    append_operator_action_event(
        action="claim-item",
        operator_id="operator-a",
        target={"review_target": "strategy:demo", "work_item_key": "work-1"},
        summary_line="claim demo work item",
    )

    payload = verify_operator_action_journal(database_path=str(database_path))

    assert payload["schema_version"] == "ledger_ops_operator_action_chain_verify/v1"
    assert payload["ok"] is True
    assert payload["event_count"] == 1
    assert payload["issue_count"] == 0


def test_ledger_ops_cli_verify_operator_actions_json(monkeypatch, tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    monkeypatch.setenv("STRATEGY_VALIDATOR_LEDGER_DB_PATH", str(database_path))
    append_operator_action_event(
        action="claim-item",
        operator_id="operator-a",
        target={"review_target": "strategy:demo", "work_item_key": "work-1"},
        summary_line="claim demo work item",
    )

    rc = main(["verify-operator-actions", "--database-path", str(database_path), "--json"])

    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["schema_version"] == "ledger_ops_operator_action_chain_verify/v1"
    assert payload["ok"] is True
    assert payload["event_count"] == 1

def test_ledger_ops_backup_rejects_symlinked_database_path(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    run_migration(database_path=str(database_path))
    linked_database = tmp_path / "linked-ledger.sqlite3"
    try:
        linked_database.symlink_to(database_path)
    except (OSError, NotImplementedError):
        return

    with pytest.raises(LedgerOpsError) as raised:
        backup_ledger_database(database_path=str(linked_database), backup_dir=str(backup_dir))

    assert "LEDGER_DATABASE_PATH_IS_SYMLINK" in str(raised.value)
    assert not backup_dir.exists()


def test_ledger_ops_backup_rejects_symlinked_backup_dir(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    real_backup_dir = tmp_path / "real-backups"
    linked_backup_dir = tmp_path / "linked-backups"
    run_migration(database_path=str(database_path))
    real_backup_dir.mkdir()
    try:
        linked_backup_dir.symlink_to(real_backup_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    with pytest.raises(LedgerOpsError) as raised:
        backup_ledger_database(database_path=str(database_path), backup_dir=str(linked_backup_dir))

    assert "LEDGER_BACKUP_DIR_IS_SYMLINK" in str(raised.value)
    assert list(real_backup_dir.iterdir()) == []


def test_ledger_ops_restore_rejects_symlinked_backup_source(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    restore_path = tmp_path / "restored.sqlite3"
    run_migration(database_path=str(database_path))
    backup = backup_ledger_database(database_path=str(database_path), backup_dir=str(backup_dir))
    linked_backup = tmp_path / "linked-backup.sqlite3"
    try:
        linked_backup.symlink_to(Path(backup["backup_path"]))
    except (OSError, NotImplementedError):
        return

    with pytest.raises(LedgerOpsError) as raised:
        restore_ledger_database(backup_path=str(linked_backup), database_path=str(restore_path))

    assert "LEDGER_RESTORE_BACKUP_PATH_IS_SYMLINK" in str(raised.value)
    assert not restore_path.exists()


def test_ledger_ops_restore_rejects_symlinked_destination_path(tmp_path: Path) -> None:
    source_database_path = tmp_path / "source-ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    real_destination = tmp_path / "real-destination.sqlite3"
    linked_destination = tmp_path / "linked-destination.sqlite3"
    run_migration(database_path=str(source_database_path))
    backup = backup_ledger_database(database_path=str(source_database_path), backup_dir=str(backup_dir))
    try:
        linked_destination.symlink_to(real_destination)
    except (OSError, NotImplementedError):
        return

    with pytest.raises(LedgerOpsError) as raised:
        restore_ledger_database(
            backup_path=backup["backup_path"],
            database_path=str(linked_destination),
            allow_overwrite=True,
            verify_after=False,
        )

    assert "LEDGER_RESTORE_DESTINATION_PATH_IS_SYMLINK" in str(raised.value)
    assert not real_destination.exists()


def test_ledger_ops_restore_rejects_symlinked_pre_restore_backup_dir(tmp_path: Path) -> None:
    source_database_path = tmp_path / "source-ledger.sqlite3"
    destination_database_path = tmp_path / "destination-ledger.sqlite3"
    backup_dir = tmp_path / "backups"
    real_pre_restore = tmp_path / "real-pre-restore"
    linked_pre_restore = tmp_path / "linked-pre-restore"
    run_migration(database_path=str(source_database_path))
    run_migration(database_path=str(destination_database_path))
    backup = backup_ledger_database(database_path=str(source_database_path), backup_dir=str(backup_dir))
    real_pre_restore.mkdir()
    try:
        linked_pre_restore.symlink_to(real_pre_restore, target_is_directory=True)
    except (OSError, NotImplementedError):
        return

    with pytest.raises(LedgerOpsError) as raised:
        restore_ledger_database(
            backup_path=backup["backup_path"],
            database_path=str(destination_database_path),
            allow_overwrite=True,
            pre_restore_backup_dir=str(linked_pre_restore),
        )

    assert "LEDGER_PRE_RESTORE_BACKUP_DIR_IS_SYMLINK" in str(raised.value)
    assert list(real_pre_restore.iterdir()) == []


def test_ledger_ops_verify_integrity_rejects_symlinked_database_path(tmp_path: Path) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    linked_database = tmp_path / "linked-ledger.sqlite3"
    run_migration(database_path=str(database_path))
    try:
        linked_database.symlink_to(database_path)
    except (OSError, NotImplementedError):
        return

    payload = verify_ledger_integrity(database_path=str(linked_database))

    assert payload["ok"] is False
    assert payload["database_sha256"] is None
    assert payload["ledger"]["path_integrity"]["ok"] is False
    assert "LEDGER_DATABASE_PATH_IS_SYMLINK" in payload["ledger"]["error"]
    assert payload["operator_actions"]["path_integrity"]["ok"] is False


def test_ledger_ops_cli_verify_integrity_rejects_symlinked_database_path(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / "ledger.sqlite3"
    linked_database = tmp_path / "linked-ledger.sqlite3"
    run_migration(database_path=str(database_path))
    try:
        linked_database.symlink_to(database_path)
    except (OSError, NotImplementedError):
        return

    rc = main(["verify-integrity", "--database-path", str(linked_database), "--json"])

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is False
    assert payload["database_sha256"] is None
    assert "LEDGER_DATABASE_PATH_IS_SYMLINK" in payload["ledger"]["error"]
