"""
Canonical test infrastructure.

Ledger isolation strategy
=========================
Every test receives its own isolated SQLite database.  The database path
is unique per test function, so there is zero risk of cross-test
interference or Windows file-lock cascades.

Two-layer fixture design:
  - isolate_ledger  (function-scoped): creates a unique temp DB path
                    and sets the environment variable.
  - clean_ledger    (function-scoped, autouse): runs *before* each test
                    to ensure the DB is empty (TRUNCATE, not unlink).
                    This avoids Windows SQLite WAL file-lock issues.

No test shares ledger state.  No cleanup relies on unlinking a file
still held by another process.
"""
import os
import sqlite3
import uuid
import tempfile
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Ledger isolation
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function")
def isolate_ledger():
    """
    Function-scoped ledger isolation.
    Each test receives a unique temporary SQLite database path.
    """
    tmp_dir = Path(tempfile.gettempdir()) / "strategy_validator_test"
    tmp_dir.mkdir(parents=True, exist_ok=True)

    # Unique DB name per test invocation
    db_name = f"ledger_{uuid.uuid4().hex}.sqlite3"
    db_path = tmp_dir / db_name

    # Set the environment variable before any ledger module is imported
    os.environ["STRATEGY_VALIDATOR_LEDGER_DB_PATH"] = str(db_path)

    # Reset mode to DEV for test isolation — tests that need PRODUCTION
    # must explicitly set it via monkeypatch.
    os.environ["STRATEGY_VALIDATOR_MODE"] = "DEV"

    yield db_path

    # Cleanup env vars
    for key in ("STRATEGY_VALIDATOR_LEDGER_DB_PATH", "STRATEGY_VALIDATOR_MODE"):
        if key in os.environ:
            del os.environ[key]

    # Attempt to remove all SQLite files (main, -wal, -shm)
    for suffix in ("", "-wal", "-shm"):
        target = Path(str(db_path) + suffix)
        try:
            if target.exists():
                target.unlink(missing_ok=True)
        except OSError:
            pass  # Best-effort; stale temp files are harmless


@pytest.fixture(autouse=True, scope="function")
def clean_ledger(isolate_ledger):
    """
    Ensures each test starts with a clean ledger state.
    Uses SQL TRUNCATE instead of file deletion to avoid Windows
    SQLite WAL file-lock issues.
    """
    db_path = isolate_ledger

    # If the DB exists from a prior test that reused this path (shouldn't
    # happen with UUID naming, but be defensive), truncate all data.
    if db_path.exists():
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("PRAGMA journal_mode=DELETE")  # Disable WAL for test cleanup
            conn.execute("DELETE FROM ledger_events")
            conn.commit()
            conn.close()
        except (sqlite3.OperationalError, Exception):
            # If the DB doesn't have the table yet, that's fine — it's empty.
            pass

    yield
