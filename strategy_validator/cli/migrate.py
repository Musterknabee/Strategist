"""Ledger migration CLI for controlled production upgrades."""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

from strategy_validator.ledger._append_only import resolve_database_path
from strategy_validator.cli.deployment_env_check import (
    absolute_path_preserving_symlink,
    symlink_components_preserving_path,
)
from strategy_validator.migrations import (
    EXPECTED_SCHEMA_VERSION,
    apply_sqlite_migrations,
    get_current_schema_version,
)

_ENV_DB_PATH = 'STRATEGY_VALIDATOR_LEDGER_DB_PATH'


def _symlink_error_code(path: Path, symlinks: tuple[Path, ...]) -> str:
    return 'MIGRATION_DATABASE_PATH_IS_SYMLINK' if path in symlinks else 'MIGRATION_DATABASE_PATH_PARENT_IS_SYMLINK'


def _path_integrity_payload(path: Path) -> dict[str, object]:
    symlinks = symlink_components_preserving_path(path)
    if not symlinks:
        return {'ok': True}
    code = _symlink_error_code(path, symlinks)
    joined = ', '.join(str(item) for item in symlinks)
    return {
        'ok': False,
        'code': code,
        'error': f'{code}: migration database path must not contain symlink components: {joined}',
        'symlink_components': [str(item) for item in symlinks],
    }


def run_migration(*, database_path: str | None = None) -> dict[str, object]:
    previous = os.environ.get(_ENV_DB_PATH)
    if database_path:
        os.environ[_ENV_DB_PATH] = database_path
    try:
        if database_path:
            resolved = absolute_path_preserving_symlink(database_path)
        else:
            try:
                resolved = absolute_path_preserving_symlink(resolve_database_path())
            except RuntimeError as exc:
                configured = os.environ.get(_ENV_DB_PATH)
                if configured and 'LEDGER_DATABASE_PATH' in str(exc):
                    resolved = absolute_path_preserving_symlink(configured)
                else:
                    raise
        path_integrity = _path_integrity_payload(resolved)
        if not path_integrity['ok']:
            return {
                'ok': False,
                'database_path': str(resolved),
                'schema_version_before': 0,
                'schema_version_after': 0,
                'expected_schema_version': EXPECTED_SCHEMA_VERSION,
                'migrated': False,
                'path_integrity': path_integrity,
                'error': path_integrity['error'],
            }
        resolved = absolute_path_preserving_symlink(resolve_database_path())
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
            'path_integrity': path_integrity,
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
