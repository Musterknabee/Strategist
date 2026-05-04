from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path


EXPECTED_SCHEMA_VERSION = 5


@dataclass(frozen=True)
class SQLiteMigrationPathError(RuntimeError):
    """Machine-readable SQLite migration path-integrity failure."""

    code: str
    path: str
    detail: str

    def __str__(self) -> str:  # pragma: no cover
        return f"{self.code}: {self.detail} ({self.path})"


def _absolute_path_preserving_symlink(path: str | Path) -> Path:
    candidate = Path(path).expanduser()
    if candidate.is_absolute():
        return candidate
    return Path.cwd() / candidate


def _symlink_components_preserving_path(path: str | Path) -> tuple[Path, ...]:
    absolute = _absolute_path_preserving_symlink(path)
    parts = absolute.parts
    if not parts:
        return ()
    current = Path(parts[0])
    candidates: list[Path] = []
    for part in parts[1:]:
        current = current / part
        candidates.append(current)
    return tuple(candidate for candidate in candidates if candidate.is_symlink())


def _raise_for_symlinks(path: Path, *, label: str) -> None:
    symlinks = _symlink_components_preserving_path(path)
    if not symlinks:
        return
    final_component = path in symlinks
    code = f"{label}_IS_SYMLINK" if final_component else f"{label}_PARENT_IS_SYMLINK"
    detail = "symlinked path" if final_component else "symlinked parent directories"
    raise SQLiteMigrationPathError(
        code=code,
        path=str(path),
        detail=f"{detail}: {', '.join(str(item) for item in symlinks)}",
    )


def _sqlite_migrations_dir() -> Path | None:
    module_path = _absolute_path_preserving_symlink(__file__)
    _raise_for_symlinks(module_path, label="SQLITE_MIGRATION_MODULE")
    migrations_dir = module_path.parent / "sqlite"
    _raise_for_symlinks(migrations_dir, label="SQLITE_MIGRATION_ROOT")
    if not migrations_dir.exists():
        return None
    if not migrations_dir.is_dir():
        raise SQLiteMigrationPathError(
            code="SQLITE_MIGRATION_ROOT_NOT_DIRECTORY",
            path=str(migrations_dir),
            detail="SQLite migration root exists but is not a directory",
        )
    return migrations_dir


def _iter_sql_migrations(migrations_dir: Path) -> tuple[Path, ...]:
    migrations: list[Path] = []
    for migration in sorted(migrations_dir.glob("*.sql")):
        _raise_for_symlinks(migration, label="SQLITE_MIGRATION_FILE")
        if not migration.is_file():
            raise SQLiteMigrationPathError(
                code="SQLITE_MIGRATION_FILE_NOT_REGULAR",
                path=str(migration),
                detail="SQLite migration path exists but is not a regular file",
            )
        migrations.append(migration)
    return tuple(migrations)


def apply_sqlite_migrations(connection: sqlite3.Connection) -> None:
    migrations_dir = _sqlite_migrations_dir()
    if migrations_dir is None:
        return
    for migration in _iter_sql_migrations(migrations_dir):
        connection.executescript(migration.read_text(encoding="utf-8"))


def get_current_schema_version(connection: sqlite3.Connection) -> int:
    """Detect current schema version from tracking table."""
    try:
        row = connection.execute(
            "SELECT MAX(version_id) FROM _schema_version_tracking"
        ).fetchone()
        return row[0] if row and row[0] is not None else 0
    except sqlite3.OperationalError:
        # Table doesn't exist yet
        return 0


__all__ = [
    "EXPECTED_SCHEMA_VERSION",
    "SQLiteMigrationPathError",
    "apply_sqlite_migrations",
    "get_current_schema_version",
]
