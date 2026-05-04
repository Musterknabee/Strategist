from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from strategy_validator import migrations
from strategy_validator.migrations import SQLiteMigrationPathError


def _module_tree(tmp_path: Path) -> Path:
    root = tmp_path / "pkg" / "strategy_validator" / "migrations"
    root.mkdir(parents=True)
    (root / "__init__.py").write_text("# placeholder\n", encoding="utf-8")
    sqlite_root = root / "sqlite"
    sqlite_root.mkdir()
    (sqlite_root / "001_schema.sql").write_text(
        "CREATE TABLE IF NOT EXISTS _schema_version_tracking "
        "(version_id INTEGER PRIMARY KEY, applied_at_utc TEXT, description TEXT);\n"
        "INSERT OR IGNORE INTO _schema_version_tracking "
        "(version_id, applied_at_utc, description) VALUES (5, 'now', 'test');\n",
        encoding="utf-8",
    )
    return root


def test_apply_sqlite_migrations_accepts_regular_tmp_migration_tree(monkeypatch, tmp_path: Path) -> None:
    module_root = _module_tree(tmp_path)
    monkeypatch.setattr(migrations, "__file__", str(module_root / "__init__.py"))

    with sqlite3.connect(":memory:") as connection:
        migrations.apply_sqlite_migrations(connection)
        assert migrations.get_current_schema_version(connection) == 5


def test_apply_sqlite_migrations_rejects_symlinked_module_path(monkeypatch, tmp_path: Path) -> None:
    module_root = _module_tree(tmp_path)
    real_module = module_root / "__init__.py"
    linked_module = tmp_path / "linked_migrations_init.py"
    linked_module.symlink_to(real_module)
    monkeypatch.setattr(migrations, "__file__", str(linked_module))

    with sqlite3.connect(":memory:") as connection, pytest.raises(SQLiteMigrationPathError) as exc_info:
        migrations.apply_sqlite_migrations(connection)

    assert exc_info.value.code == "SQLITE_MIGRATION_MODULE_IS_SYMLINK"


def test_apply_sqlite_migrations_rejects_symlinked_sqlite_root(monkeypatch, tmp_path: Path) -> None:
    module_root = _module_tree(tmp_path)
    real_sqlite = tmp_path / "real_sqlite"
    (module_root / "sqlite").rename(real_sqlite)
    (module_root / "sqlite").symlink_to(real_sqlite, target_is_directory=True)
    monkeypatch.setattr(migrations, "__file__", str(module_root / "__init__.py"))

    with sqlite3.connect(":memory:") as connection, pytest.raises(SQLiteMigrationPathError) as exc_info:
        migrations.apply_sqlite_migrations(connection)

    assert exc_info.value.code == "SQLITE_MIGRATION_ROOT_IS_SYMLINK"


def test_apply_sqlite_migrations_rejects_symlinked_sql_file(monkeypatch, tmp_path: Path) -> None:
    module_root = _module_tree(tmp_path)
    sqlite_root = module_root / "sqlite"
    outside_sql = tmp_path / "outside.sql"
    outside_sql.write_text("CREATE TABLE leaked(value TEXT);\n", encoding="utf-8")
    (sqlite_root / "002_linked.sql").symlink_to(outside_sql)
    monkeypatch.setattr(migrations, "__file__", str(module_root / "__init__.py"))

    with sqlite3.connect(":memory:") as connection, pytest.raises(SQLiteMigrationPathError) as exc_info:
        migrations.apply_sqlite_migrations(connection)

    assert exc_info.value.code == "SQLITE_MIGRATION_FILE_IS_SYMLINK"


def test_migration_truth_check_reports_runtime_migration_path_integrity(monkeypatch, tmp_path: Path) -> None:
    from scripts.migration_truth_check import run_migration_truth_check

    module_root = _module_tree(tmp_path)
    outside_sql = tmp_path / "outside.sql"
    outside_sql.write_text("CREATE TABLE leaked(value TEXT);\n", encoding="utf-8")
    (module_root / "sqlite" / "002_linked.sql").symlink_to(outside_sql)
    monkeypatch.setattr(migrations, "__file__", str(module_root / "__init__.py"))

    report = run_migration_truth_check()
    payload = report.to_payload()

    assert payload["status"] == "FAIL"
    assert payload["failures"][0]["name"] == "sqlite_migration_path_integrity"
    assert "SQLITE_MIGRATION_FILE_IS_SYMLINK" in payload["failures"][0]["detail"]
