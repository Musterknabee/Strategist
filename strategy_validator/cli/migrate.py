"""Ledger migration CLI for controlled production upgrades."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from strategy_validator.ledger._append_only import resolve_database_path
from strategy_validator.migrations import (
    EXPECTED_SCHEMA_VERSION,
    apply_sqlite_migrations,
    get_current_schema_version,
)

_ENV_DB_PATH = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH'


def run_migration(*, database_path: str | None = None) -> dict[str, object]:
    previous = os.environ.get(_ENV_DB_PATH)
    if database_path:
        os.environ[_ENV_DB_PATH] = database_path
    try:
        resolved = resolve_database_path()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(resolved) as connection:
            before = get_current_schema_version(connection)
            apply_sqlite_migrations(connection)
            connection.commit()
            after = get_current_schema_version(connection)
        return {
            'ok': after == EXPECTED_SCHEMA_VERSION,
            'database_path': str(resolved),
            'schema_version_before': before,
            'schema_version_after': after,
            'expected_schema_version': EXPECTED_SCHEMA_VERSION,
            'migrated': after != before,
        }
    finally:
        if database_path:
            if previous is None:
                os.environ.pop(_ENV_DB_PATH, None)
            else:
                os.environ[_ENV_DB_PATH] = previous


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Upgrade the strategy-validator forensic ledger schema')
    parser.add_argument('--database-path', default='', help='Absolute or explicit SQLite path to upgrade')
    parser.add_argument('--json', action='store_true', help='Emit structured JSON status')
    ns = parser.parse_args(argv)

    payload = run_migration(database_path=ns.database_path or None)
    if ns.json:
        sys.stdout.write(json.dumps(payload, indent=2) + '\n')
    else:
        sys.stdout.write(
            'strategy-validator ledger migration\n'
            f"database_path={payload['database_path']}\n"
            f"schema_version_before={payload['schema_version_before']}\n"
            f"schema_version_after={payload['schema_version_after']}\n"
            f"expected_schema_version={payload['expected_schema_version']}\n"
            f"migrated={'yes' if payload['migrated'] else 'no'}\n"
        )
    sys.stdout.flush()
    return 0 if payload['ok'] else 1


if __name__ == '__main__':  # pragma: no cover
    raise SystemExit(main())
