"""Guardrails: SQLite ledger migrations must ship in the sdist/wheel (package-data)."""
from __future__ import annotations

import tomllib
from pathlib import Path

from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION

ROOT = Path(__file__).resolve().parents[2]


def test_sqlite_migration_file_count_matches_expected_schema_version():
    sqlite_dir = ROOT / "strategy_validator" / "migrations" / "sqlite"
    sql_files = sorted(sqlite_dir.glob("*.sql"))
    assert len(sql_files) == EXPECTED_SCHEMA_VERSION, (
        f"EXPECTED_SCHEMA_VERSION={EXPECTED_SCHEMA_VERSION} but found {len(sql_files)} *.sql under {sqlite_dir}"
    )


def test_pyproject_declares_package_data_for_sqlite_migrations():
    raw = (ROOT / "pyproject.toml").read_bytes()
    data = tomllib.loads(raw.decode())
    pkg_data = data.get("tool", {}).get("setuptools", {}).get("package-data", {})
    patterns = pkg_data.get("strategy_validator", [])
    assert "migrations/sqlite/*.sql" in patterns, patterns
