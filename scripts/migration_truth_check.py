from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

# This gate is part of the fast release path. It should be safe to run from a
# source archive before package installation and should not leave bytecode behind.
sys.dont_write_bytecode = True

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, safe_input_dir
from strategy_validator.migrations import (
    EXPECTED_SCHEMA_VERSION,
    SQLiteMigrationPathError,
    apply_sqlite_migrations,
    get_current_schema_version,
)

REQUIRED_TABLES = (
    "ledger_events",
    "operator_action_events",
    "_schema_version_tracking",
)
REQUIRED_INDEXES = (
    "idx_operator_action_events_operator_created",
    "idx_operator_action_events_sequence",
    "idx_operator_action_events_sequence_unique",
    "idx_operator_action_events_idempotency_key",
    "idx_operator_action_events_idempotency_key_unique",
)
REQUIRED_COLUMNS: dict[str, tuple[str, ...]] = {
    "ledger_events": (
        "experiment_id",
        "sequence_number",
        "event_type",
        "promotion_state",
        "event_payload_json",
        "manifest_hash",
        "event_hash",
        "previous_event_hash",
        "created_at_utc",
        "writer_identity",
    ),
    "operator_action_events": (
        "action_event_id",
        "action",
        "operator_id",
        "target_payload_json",
        "accepted",
        "status",
        "summary_line",
        "created_at_utc",
        "event_hash",
        "sequence_number",
        "previous_event_hash",
    ),
    "_schema_version_tracking": (
        "version_id",
        "applied_at_utc",
        "description",
    ),
}
REQUIRED_UNIQUE_INDEXES = (
    "idx_operator_action_events_sequence_unique",
    "idx_operator_action_events_idempotency_key_unique",
)


@dataclass(frozen=True)
class MigrationTruthFailure:
    name: str
    detail: str


@dataclass(frozen=True)
class MigrationTruthReport:
    schema_version: str
    status: str
    expected_schema_version: int
    first_schema_version: int
    second_schema_version: int
    table_count: int
    index_count: int
    column_contract_count: int
    idempotency_uniqueness_enforced: bool
    sequence_uniqueness_enforced: bool
    failure_count: int
    failures: tuple[MigrationTruthFailure, ...]

    def to_payload(self) -> dict[str, object]:
        return asdict(self)


def _sqlite_names(connection: sqlite3.Connection, *, kind: str) -> set[str]:
    rows = connection.execute(
        "SELECT name FROM sqlite_master WHERE type = ? AND name NOT LIKE 'sqlite_%'",
        (kind,),
    ).fetchall()
    return {str(row[0]) for row in rows}


def _table_columns(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row[1]) for row in rows}


def _unique_indexes(connection: sqlite3.Connection, table_name: str) -> set[str]:
    rows = connection.execute(f"PRAGMA index_list({table_name})").fetchall()
    unique: set[str] = set()
    for row in rows:
        # row shape: seq, name, unique, origin, partial
        if int(row[2]) == 1:
            unique.add(str(row[1]))
    return unique


def _sequence_uniqueness_is_enforced(connection: sqlite3.Connection) -> bool:
    base = (
        "INSERT INTO operator_action_events ("
        "action_event_id, action, operator_id, target_payload_json, accepted, status, "
        "summary_line, created_at_utc, event_hash, sequence_number, previous_event_hash"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    connection.execute(
        base,
        (
            "seq-evt-1",
            "claim-item",
            "operator",
            '{"work_item_key":"wk-1"}',
            1,
            "accepted",
            "first",
            "2026-01-01T00:00:00+00:00",
            "c" * 64,
            10,
            None,
        ),
    )
    try:
        connection.execute(
            base,
            (
                "seq-evt-2",
                "claim-item",
                "operator",
                '{"work_item_key":"wk-2"}',
                1,
                "accepted",
                "second",
                "2026-01-01T00:00:01+00:00",
                "d" * 64,
                10,
                "c" * 64,
            ),
        )
    except sqlite3.IntegrityError:
        return True
    return False


def _idempotency_uniqueness_is_enforced(connection: sqlite3.Connection) -> bool:
    payload = '{"idempotency_key":"same-key"}'
    base = (
        "INSERT INTO operator_action_events ("
        "action_event_id, action, operator_id, target_payload_json, accepted, status, "
        "summary_line, created_at_utc, event_hash, sequence_number, previous_event_hash"
        ") VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    connection.execute(
        base,
        (
            "evt-1",
            "claim-item",
            "operator",
            payload,
            1,
            "accepted",
            "first",
            "2026-01-01T00:00:00+00:00",
            "a" * 64,
            1,
            None,
        ),
    )
    try:
        connection.execute(
            base,
            (
                "evt-2",
                "claim-item",
                "operator",
                payload,
                1,
                "accepted",
                "second",
                "2026-01-01T00:00:01+00:00",
                "b" * 64,
                2,
                "a" * 64,
            ),
        )
    except sqlite3.IntegrityError:
        return True
    return False


def _failed_path_integrity_report(exc: PathIntegrityError) -> MigrationTruthReport:
    failure = MigrationTruthFailure(name="repo_root_path_integrity", detail=f"{exc.code}: {exc.detail} ({exc.path})")
    return MigrationTruthReport(
        schema_version="migration_truth_check/v3",
        status="FAIL",
        expected_schema_version=EXPECTED_SCHEMA_VERSION,
        first_schema_version=0,
        second_schema_version=0,
        table_count=0,
        index_count=0,
        column_contract_count=0,
        idempotency_uniqueness_enforced=False,
        sequence_uniqueness_enforced=False,
        failure_count=1,
        failures=(failure,),
    )


def run_migration_truth_check(*, repo_root: str | Path | None = None) -> MigrationTruthReport:
    # repo_root is accepted for CLI symmetry and future extension. The migration
    # implementation is imported from source above, so this check intentionally
    # exercises the currently checked-out package code. Still, explicit repo-root
    # values must not be followed through symlinks: this gate is part of the same
    # release evidence chain as source_health and repository_truth_check.
    try:
        if repo_root is not None:
            safe_input_dir(repo_root, label="MIGRATION_TRUTH_REPO_ROOT")
    except PathIntegrityError as exc:
        return _failed_path_integrity_report(exc)

    failures: list[MigrationTruthFailure] = []
    idempotency_uniqueness_enforced = False
    sequence_uniqueness_enforced = False
    try:
        with sqlite3.connect(":memory:") as connection:
            apply_sqlite_migrations(connection)
            connection.commit()
            first_schema_version = get_current_schema_version(connection)
            apply_sqlite_migrations(connection)
            connection.commit()
            second_schema_version = get_current_schema_version(connection)
            tables = _sqlite_names(connection, kind="table")
            indexes = _sqlite_names(connection, kind="index")
            column_contract_count = 0
            for table_name, required_columns in REQUIRED_COLUMNS.items():
                existing_columns = _table_columns(connection, table_name)
                missing_columns = sorted(set(required_columns) - existing_columns)
                column_contract_count += len(required_columns)
                if missing_columns:
                    failures.append(
                        MigrationTruthFailure(
                            name=f"required_columns:{table_name}",
                            detail=", ".join(missing_columns),
                        )
                    )
            unique_indexes = _unique_indexes(connection, "operator_action_events")
            missing_unique_indexes = sorted(set(REQUIRED_UNIQUE_INDEXES) - unique_indexes)
            if missing_unique_indexes:
                failures.append(MigrationTruthFailure(name="required_unique_indexes", detail=", ".join(missing_unique_indexes)))
            sequence_uniqueness_enforced = _sequence_uniqueness_is_enforced(connection)
            idempotency_uniqueness_enforced = _idempotency_uniqueness_is_enforced(connection)
    except SQLiteMigrationPathError as exc:
        failures.append(MigrationTruthFailure(name="sqlite_migration_path_integrity", detail=str(exc)))
        return MigrationTruthReport(
            schema_version="migration_truth_check/v3",
            status="FAIL",
            expected_schema_version=EXPECTED_SCHEMA_VERSION,
            first_schema_version=0,
            second_schema_version=0,
            table_count=0,
            index_count=0,
            column_contract_count=0,
            idempotency_uniqueness_enforced=False,
            sequence_uniqueness_enforced=False,
            failure_count=len(failures),
            failures=tuple(failures),
        )

    if first_schema_version != EXPECTED_SCHEMA_VERSION:
        failures.append(
            MigrationTruthFailure(
                name="first_apply_schema_version",
                detail=f"first apply produced schema version {first_schema_version}, expected {EXPECTED_SCHEMA_VERSION}",
            )
        )
    if second_schema_version != EXPECTED_SCHEMA_VERSION:
        failures.append(
            MigrationTruthFailure(
                name="second_apply_schema_version",
                detail=f"second apply produced schema version {second_schema_version}, expected {EXPECTED_SCHEMA_VERSION}",
            )
        )
    if second_schema_version != first_schema_version:
        failures.append(
            MigrationTruthFailure(
                name="migration_idempotency",
                detail=f"schema version changed on second apply: {first_schema_version} -> {second_schema_version}",
            )
        )

    missing_tables = sorted(set(REQUIRED_TABLES) - tables)
    if missing_tables:
        failures.append(MigrationTruthFailure(name="required_tables", detail=", ".join(missing_tables)))
    missing_indexes = sorted(set(REQUIRED_INDEXES) - indexes)
    if missing_indexes:
        failures.append(MigrationTruthFailure(name="required_indexes", detail=", ".join(missing_indexes)))
    if not sequence_uniqueness_enforced:
        failures.append(
            MigrationTruthFailure(
                name="operator_action_sequence_uniqueness",
                detail="duplicate non-null operator action sequence numbers were accepted by SQLite",
            )
        )
    if not idempotency_uniqueness_enforced:
        failures.append(
            MigrationTruthFailure(
                name="operator_action_idempotency_uniqueness",
                detail="duplicate non-empty idempotency keys were accepted by SQLite",
            )
        )

    return MigrationTruthReport(
        schema_version="migration_truth_check/v3",
        status="PASS" if not failures else "FAIL",
        expected_schema_version=EXPECTED_SCHEMA_VERSION,
        first_schema_version=first_schema_version,
        second_schema_version=second_schema_version,
        table_count=len(tables),
        index_count=len(indexes),
        column_contract_count=column_contract_count,
        idempotency_uniqueness_enforced=idempotency_uniqueness_enforced,
        sequence_uniqueness_enforced=sequence_uniqueness_enforced,
        failure_count=len(failures),
        failures=tuple(failures),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate SQLite migration truth and idempotency without touching local ledger files.")
    parser.add_argument("--repo-root", default=None, help="Repository root; accepted for consistency with other repo gates")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    args = parser.parse_args(argv)

    report = run_migration_truth_check(repo_root=args.repo_root)
    payload = report.to_payload()
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(
            f"migration_truth_check: {report.status} expected={report.expected_schema_version} "
            f"first={report.first_schema_version} second={report.second_schema_version} "
            f"sequence_unique={report.sequence_uniqueness_enforced} "
            f"idempotency_unique={report.idempotency_uniqueness_enforced}"
        )
        for failure in report.failures:
            print(f"{failure.name}: {failure.detail}")
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
