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
