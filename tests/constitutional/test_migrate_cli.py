from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from strategy_validator.cli.migrate import main
from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION, get_current_schema_version


def test_strategy_validator_migrate_upgrades_explicit_sqlite_path(tmp_path: Path, capsys) -> None:
    database_path = tmp_path / 'ledger.sqlite3'
    rc = main(['--database-path', str(database_path), '--json'])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload['expected_schema_version'] == EXPECTED_SCHEMA_VERSION
    assert payload['schema_version_after'] == EXPECTED_SCHEMA_VERSION
    with sqlite3.connect(database_path) as connection:
        assert get_current_schema_version(connection) == EXPECTED_SCHEMA_VERSION


def test_strategy_validator_migrate_rejects_symlinked_database_path(tmp_path: Path, capsys) -> None:
    real_database_path = tmp_path / 'real-ledger.sqlite3'
    linked_database_path = tmp_path / 'linked-ledger.sqlite3'
    try:
        linked_database_path.symlink_to(real_database_path)
    except (OSError, NotImplementedError):
        return

    rc = main(['--database-path', str(linked_database_path), '--json'])

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload['ok'] is False
    assert payload['path_integrity']['ok'] is False
    assert payload['path_integrity']['code'] == 'MIGRATION_DATABASE_PATH_IS_SYMLINK'
    assert not real_database_path.exists()


def test_strategy_validator_migrate_rejects_database_path_under_symlinked_parent(tmp_path: Path, capsys) -> None:
    real_dir = tmp_path / 'real-ledger-dir'
    linked_dir = tmp_path / 'linked-ledger-dir'
    real_dir.mkdir()
    try:
        linked_dir.symlink_to(real_dir, target_is_directory=True)
    except (OSError, NotImplementedError):
        return
    database_path = linked_dir / 'ledger.sqlite3'

    rc = main(['--database-path', str(database_path), '--json'])

    assert rc == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload['ok'] is False
    assert payload['path_integrity']['ok'] is False
    assert payload['path_integrity']['code'] == 'MIGRATION_DATABASE_PATH_PARENT_IS_SYMLINK'
    assert not (real_dir / 'ledger.sqlite3').exists()
