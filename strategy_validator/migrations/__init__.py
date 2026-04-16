from __future__ import annotations

import sqlite3
from pathlib import Path


EXPECTED_SCHEMA_VERSION = 2

def apply_sqlite_migrations(connection: sqlite3.Connection) -> None:
    migrations_dir = Path(__file__).resolve().parent / "sqlite"
    if not migrations_dir.exists():
        return
    for migration in sorted(migrations_dir.glob("*.sql")):
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
