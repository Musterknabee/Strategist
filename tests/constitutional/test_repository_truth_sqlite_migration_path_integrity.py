from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts import repository_truth_check as rtc
from scripts._path_integrity import PathIntegrityError
from scripts.repository_truth_check import _safe_sqlite_migration_files


def _minimal_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    migrations_pkg = repo / "strategy_validator" / "migrations"
    migrations_pkg.mkdir(parents=True)
    (migrations_pkg / "__init__.py").write_text("EXPECTED_SCHEMA_VERSION = 1\n", encoding="utf-8")
    return repo


def test_repository_truth_rejects_symlinked_sqlite_migration_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    outside_sqlite = tmp_path / "outside-sqlite"
    outside_sqlite.mkdir()
    (outside_sqlite / "9999_external.sql").write_text(
        "INSERT OR IGNORE INTO _schema_version_tracking (version_id, applied_at_utc, description) "
        "VALUES (9999, datetime('now'), 'external');\n",
        encoding="utf-8",
    )
    (repo / "strategy_validator" / "migrations" / "sqlite").symlink_to(outside_sqlite, target_is_directory=True)

    with pytest.raises(PathIntegrityError) as exc_info:
        _safe_sqlite_migration_files(repo)

    assert exc_info.value.code == "REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_IS_SYMLINK"


def test_repository_truth_rejects_sqlite_migration_root_under_symlinked_parent(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_migrations = tmp_path / "real-migrations"
    real_migrations.mkdir()
    (real_migrations / "sqlite").mkdir()
    migrations_path = repo / "strategy_validator" / "migrations"
    shutil.rmtree(migrations_path)
    migrations_path.symlink_to(real_migrations, target_is_directory=True)

    try:
        with pytest.raises(PathIntegrityError) as exc_info:
            _safe_sqlite_migration_files(repo)

        assert exc_info.value.code == "REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_PARENT_IS_SYMLINK"
    finally:
        if migrations_path.is_symlink():
            migrations_path.unlink()


def test_repository_truth_rejects_symlinked_sqlite_migration_file(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    sqlite_root = repo / "strategy_validator" / "migrations" / "sqlite"
    sqlite_root.mkdir()
    outside_sql = tmp_path / "outside.sql"
    outside_sql.write_text("CREATE TABLE leaked(value TEXT);\n", encoding="utf-8")
    (sqlite_root / "0002_linked.sql").symlink_to(outside_sql)

    with pytest.raises(PathIntegrityError) as exc_info:
        _safe_sqlite_migration_files(repo)

    assert exc_info.value.code == "REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_IS_SYMLINK"


def test_repository_truth_reports_sqlite_migration_path_integrity_failure(monkeypatch, tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    sqlite_root = repo / "strategy_validator" / "migrations" / "sqlite"
    sqlite_root.mkdir()
    outside_sql = tmp_path / "outside.sql"
    outside_sql.write_text("CREATE TABLE leaked(value TEXT);\n", encoding="utf-8")
    (sqlite_root / "0002_linked.sql").symlink_to(outside_sql)

    original_read_text = rtc._read_text

    def tolerant_read_text(path: Path) -> str:
        if not path.exists():
            return ""
        return original_read_text(path)

    monkeypatch.setattr(rtc, "_read_text", tolerant_read_text)

    report = rtc.run_repository_truth_check(repo_root=repo)
    checks = {check["name"]: check for check in report.to_payload()["checks"]}

    assert report.status == "FAIL"
    assert checks["sqlite_migration_path_integrity"]["status"] == "FAIL"
    assert "REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_IS_SYMLINK" in checks["sqlite_migration_path_integrity"]["detail"]
