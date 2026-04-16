"""Internal durable append-only event log; import only from ledger.reader / ledger.writer."""

from __future__ import annotations

import json
import os
import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path, PureWindowsPath
import re
import tempfile
from typing import Any

from strategy_validator.core.exceptions import ImmutableViolation
from strategy_validator.migrations import apply_sqlite_migrations

_ENV_DB_PATH = "STRATEGY_VALIDATOR_LEDGER_DB_PATH"
_DEFAULT_DB_DIR = ".strategy_validator"
_DEFAULT_DB_NAME = "ledger.sqlite3"
_TABLE_NAME = "ledger_events"
_ALLOWED_WRITE_PREFIX = f"INSERT INTO {_TABLE_NAME}".upper()
_WINDOWS_ABS_RE = re.compile(r"^[A-Za-z]:[\/].+")
_STORAGE_BACKEND = "sqlite_single_node"
_STORAGE_UPGRADE_STATUS = "PATH_DECLARED_NOT_IMPLEMENTED"
_STORAGE_UPGRADE_SUMMARY = (
    "Current ledger backend remains single-node SQLite. "
    "Upgrade path is governed backup, explicit migration, and append-only export/import planning before any backend change."
)


def _is_windows_absolute(path_str: str) -> bool:
    return bool(_WINDOWS_ABS_RE.match(path_str))


def _coerce_database_path(configured: str | None) -> Path:
    if configured:
        raw = str(configured)
        if _is_windows_absolute(raw):
            win = PureWindowsPath(raw)
            # Preserve drive/root semantics on non-Windows by mapping into a dedicated temp root.
            if os.name != "nt":
                parts = [p for p in win.parts[1:] if p not in ("\\", "/")]
                drive = win.drive.rstrip(":") or "drive"
                return Path(tempfile.gettempdir()) / "strategy_validator_windows_abs" / drive / Path(*parts)
            return Path(raw)
        return Path(raw)
    return Path.cwd() / _DEFAULT_DB_DIR / _DEFAULT_DB_NAME


def _is_effectively_absolute(path: Path, configured: str | None) -> bool:
    return path.is_absolute() or (bool(configured) and _is_windows_absolute(str(configured)))



@dataclass(frozen=True)
class LedgerEvent:
    experiment_id: str
    sequence_number: int
    event_type: str
    promotion_state: str
    event_payload_json: str
    manifest_hash: str
    event_hash: str
    previous_event_hash: str | None
    created_at_utc: datetime
    writer_identity: str

    @property
    def event_payload(self) -> dict[str, Any]:
        return json.loads(self.event_payload_json)


def resolve_database_path() -> Path:
    from strategy_validator.core.config import load_config
    
    config = load_config()
    configured = os.environ.get(_ENV_DB_PATH)
    path = _coerce_database_path(configured)

    if config.runtime_policy.require_absolute_ledger_path:
        is_default = not configured and (path.name == _DEFAULT_DB_NAME and path.parent.name == _DEFAULT_DB_DIR)
        if not _is_effectively_absolute(path, configured):
            raise RuntimeError(f"UNSAFE_LEDGER_PATH: Production requires an absolute path. Got: {configured or path}")
        if is_default:
            raise RuntimeError(f"DEFAULT_LEDGER_PATH_FORBIDDEN: Production cannot use default local path {path}")

    return path


def _connect() -> sqlite3.Connection:
    database_path = resolve_database_path()
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA journal_mode=WAL")
    apply_sqlite_migrations(connection)
    return connection


def _row_to_event(row: sqlite3.Row) -> LedgerEvent:
    return LedgerEvent(
        experiment_id=row["experiment_id"],
        sequence_number=row["sequence_number"],
        event_type=row["event_type"],
        promotion_state=row["promotion_state"],
        event_payload_json=row["event_payload_json"],
        manifest_hash=row["manifest_hash"],
        event_hash=row["event_hash"],
        previous_event_hash=row["previous_event_hash"],
        created_at_utc=datetime.fromisoformat(row["created_at_utc"]),
        writer_identity=row["writer_identity"],
    )


def _execute_write(statement: str, parameters: tuple[Any, ...]) -> None:
    if not statement.lstrip().upper().startswith(_ALLOWED_WRITE_PREFIX):
        raise ImmutableViolation("Ledger only permits append-only INSERT operations.")
    with _connect() as connection:
        connection.execute(statement, parameters)
        connection.commit()


def append_event(event: LedgerEvent) -> None:
    _execute_write(
        f"""
        INSERT INTO {_TABLE_NAME} (
            experiment_id,
            sequence_number,
            event_type,
            promotion_state,
            event_payload_json,
            manifest_hash,
            event_hash,
            previous_event_hash,
            created_at_utc,
            writer_identity
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            event.experiment_id,
            event.sequence_number,
            event.event_type,
            event.promotion_state,
            event.event_payload_json,
            event.manifest_hash,
            event.event_hash,
            event.previous_event_hash,
            event.created_at_utc.isoformat(),
            event.writer_identity,
        ),
    )


def read_events(experiment_id: str | None = None) -> tuple[LedgerEvent, ...]:
    statement = (
        f"SELECT * FROM {_TABLE_NAME} WHERE experiment_id = ? ORDER BY sequence_number ASC"
        if experiment_id
        else f"SELECT * FROM {_TABLE_NAME} ORDER BY experiment_id ASC, sequence_number ASC"
    )
    parameters: tuple[Any, ...] = (experiment_id,) if experiment_id else ()
    with _connect() as connection:
        rows = connection.execute(statement, parameters).fetchall()
    return tuple(_row_to_event(row) for row in rows)


def read_latest_event(experiment_id: str) -> LedgerEvent | None:
    with _connect() as connection:
        row = connection.execute(
            f"""
            SELECT * FROM {_TABLE_NAME}
            WHERE experiment_id = ?
            ORDER BY sequence_number DESC
            LIMIT 1
            """,
            (experiment_id,),
        ).fetchone()
    return None if row is None else _row_to_event(row)
def get_schema_version_info() -> tuple[int, int]:
    """Return (current_version, expected_version) from the ledger safely."""
    from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION, get_current_schema_version
    try:
        with _connect() as conn:
            current = get_current_schema_version(conn)
            return current, EXPECTED_SCHEMA_VERSION
    except Exception:
        return 0, EXPECTED_SCHEMA_VERSION


def get_storage_posture() -> dict[str, str]:
    return {
        "storage_backend": _STORAGE_BACKEND,
        "storage_upgrade_status": _STORAGE_UPGRADE_STATUS,
        "storage_upgrade_summary": _STORAGE_UPGRADE_SUMMARY,
    }
