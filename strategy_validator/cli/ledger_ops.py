"""Operator-safe ledger operations: verify, backup, and verified restore."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.ledger._append_only import resolve_database_path
from strategy_validator.cli.deployment_env_check import (
    absolute_path_preserving_symlink,
    symlink_components_preserving_path,
)
from strategy_validator.ledger.reader import verify_hash_chain, verify_hash_chain_readonly
from strategy_validator.ledger.operator_actions import verify_operator_action_event_chain_readonly
from strategy_validator.projections.operator_action_event_index import (
    build_operator_action_event_projection_index,
    write_operator_action_event_projection_index,
)
from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION, get_current_schema_version

_ENV_DB_PATH = "STRATEGY_VALIDATOR_LEDGER_DB_PATH"


class LedgerOpsError(RuntimeError):
    """Raised when an operator-safe ledger operation cannot complete."""


def _with_database_path(database_path: str | None):
    class _Ctx:
        def __enter__(self):
            self.previous = os.environ.get(_ENV_DB_PATH)
            if database_path:
                os.environ[_ENV_DB_PATH] = database_path
            return self

        def __exit__(self, exc_type, exc, tb):
            if database_path:
                if self.previous is None:
                    os.environ.pop(_ENV_DB_PATH, None)
                else:
                    os.environ[_ENV_DB_PATH] = self.previous
            return False

    return _Ctx()


def _timestamp_slug() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()



def _symlink_code(label: str, *, final_component: bool) -> str:
    return f"{label}_IS_SYMLINK" if final_component else f"{label}_PARENT_IS_SYMLINK"


def _ensure_not_symlinked(path: str | Path, *, label: str) -> Path:
    """Return an absolute path while rejecting symlinked durable ledger paths.

    Ledger operations are break-glass/operator primitives.  They must not hash,
    back up, restore, or preserve files through filesystem indirection because
    that can make evidence point somewhere other than the reviewed deployment
    volume.  Unlike ``Path.resolve()``, this preserves the operator-provided
    path so symlinks remain observable.
    """

    target = absolute_path_preserving_symlink(path)
    symlinks = symlink_components_preserving_path(target)
    if symlinks:
        final_component = target in symlinks
        code = _symlink_code(label, final_component=final_component)
        joined = ", ".join(str(item) for item in symlinks)
        raise LedgerOpsError(f"{code}: {label.lower()} must not contain symlink components: {joined}")
    return target


def _database_path_for_operation(*, label: str) -> Path:
    """Resolve the runtime ledger path while preserving operation-specific errors."""

    try:
        return _ensure_not_symlinked(resolve_database_path(), label=label)
    except RuntimeError as exc:
        configured = os.environ.get(_ENV_DB_PATH)
        if configured and "LEDGER_DATABASE_PATH" in str(exc):
            return _ensure_not_symlinked(configured, label=label)
        raise


def _ensure_regular_file(path: Path, *, label: str) -> None:
    if not path.exists():
        raise LedgerOpsError(f"{label}_MISSING: path does not exist: {path}")
    if not path.is_file():
        raise LedgerOpsError(f"{label}_NOT_FILE: path is not a regular file: {path}")


def _ensure_directory_path(path: Path, *, label: str, create: bool) -> None:
    if create:
        path.mkdir(parents=True, exist_ok=True)
    if path.exists() and not path.is_dir():
        raise LedgerOpsError(f"{label}_NOT_DIRECTORY: path is not a directory: {path}")

def verify_ledger(*, database_path: str | None = None, experiment_id: str | None = None) -> dict[str, Any]:
    """Verify schema version and hash-chain integrity for the configured ledger."""
    with _with_database_path(database_path):
        try:
            resolved = _database_path_for_operation(label="LEDGER_DATABASE_PATH")
        except LedgerOpsError as exc:
            target = absolute_path_preserving_symlink(os.environ.get(_ENV_DB_PATH, ""))
            return {
                "schema_version": "ledger_ops_verify/v1",
                "ok": False,
                "database_path": str(target),
                "database_exists": target.exists(),
                "current_schema_version": 0,
                "expected_schema_version": EXPECTED_SCHEMA_VERSION,
                "hash_chain": None,
                "path_integrity": {"ok": False, "error": str(exc)},
                "error": str(exc),
            }
        schema_version = 0
        if resolved.exists():
            with sqlite3.connect(resolved) as connection:
                schema_version = get_current_schema_version(connection)
        chain = verify_hash_chain_readonly(experiment_id) if resolved.exists() else None
        ok = resolved.exists() and schema_version >= EXPECTED_SCHEMA_VERSION and chain is not None and chain.ok
        return {
            "schema_version": "ledger_ops_verify/v1",
            "ok": ok,
            "database_path": str(resolved),
            "database_exists": resolved.exists(),
            "current_schema_version": schema_version,
            "expected_schema_version": EXPECTED_SCHEMA_VERSION,
            "hash_chain": chain.to_payload() if chain is not None else None,
            "path_integrity": {"ok": True},
        }


def verify_operator_action_journal(*, database_path: str | None = None) -> dict[str, Any]:
    """Verify append-only operator action event chain integrity."""
    with _with_database_path(database_path):
        try:
            resolved = _database_path_for_operation(label="LEDGER_DATABASE_PATH")
        except LedgerOpsError as exc:
            target = absolute_path_preserving_symlink(os.environ.get(_ENV_DB_PATH, ""))
            return {
                "schema_version": "ledger_ops_operator_action_chain_verify/v1",
                "ok": False,
                "database_path": str(target),
                "database_exists": target.exists(),
                "event_count": 0,
                "issue_count": 1,
                "issues": [str(exc)],
                "path_integrity": {"ok": False, "error": str(exc)},
            }
        report = verify_operator_action_event_chain_readonly() if resolved.exists() else None
        return {
            "schema_version": "ledger_ops_operator_action_chain_verify/v1",
            "ok": bool(resolved.exists() and report is not None and report.ok),
            "database_path": str(resolved),
            "database_exists": resolved.exists(),
            "event_count": 0 if report is None else report.event_count,
            "issue_count": 1 if report is None else report.issue_count,
            "issues": ["ledger database does not exist"] if report is None else list(report.issues),
            "path_integrity": {"ok": True},
        }




def verify_ledger_integrity(*, database_path: str | None = None, experiment_id: str | None = None) -> dict[str, Any]:
    """Verify all durable append-only ledger integrity surfaces in one JSON report.

    This is the target-host friendly report shape used by the generated
    single-tenant bundle.  It avoids writing multiple JSON documents to one
    redirected file while still checking both the adjudication ledger hash-chain
    and the operator action journal chain.
    """

    ledger = verify_ledger(database_path=database_path, experiment_id=experiment_id)
    operator_actions = verify_operator_action_journal(database_path=database_path)
    resolved = Path(str(ledger.get("database_path", ""))).expanduser()
    path_integrity_ok = bool((ledger.get("path_integrity") or {}).get("ok"))
    database_sha256 = _sha256_file(resolved) if path_integrity_ok and resolved.exists() and resolved.is_file() else None
    return {
        "schema_version": "ledger_ops_integrity_verify/v1",
        "ok": bool(ledger.get("ok") and operator_actions.get("ok")),
        "database_path": str(resolved),
        "database_exists": bool(ledger.get("database_exists")),
        "database_sha256": database_sha256,
        "ledger": ledger,
        "operator_actions": operator_actions,
    }


def backup_ledger_database(
    *,
    database_path: str | None = None,
    backup_dir: str | None = None,
    verify_before: bool = True,
    verify_after: bool = True,
) -> dict[str, Any]:
    """Create a timestamped SQLite backup and verify hash-chain integrity."""
    with _with_database_path(database_path):
        resolved = _database_path_for_operation(label="LEDGER_DATABASE_PATH")
        _ensure_regular_file(resolved, label="LEDGER_DATABASE_PATH")

        before = verify_ledger(database_path=str(resolved)) if verify_before else {"ok": True}
        if verify_before and not before["ok"]:
            raise LedgerOpsError("Refusing to back up ledger with failed pre-backup verification.")

        target_dir = _ensure_not_symlinked(backup_dir if backup_dir else resolved.parent / "backups", label="LEDGER_BACKUP_DIR")
        _ensure_directory_path(target_dir, label="LEDGER_BACKUP_DIR", create=True)
        backup_path = target_dir / f"{resolved.stem}.{_timestamp_slug()}.sqlite3"

        with sqlite3.connect(resolved) as source, sqlite3.connect(backup_path) as destination:
            source.backup(destination)

        after = verify_ledger(database_path=str(backup_path)) if verify_after else {"ok": True}
        if verify_after and not after["ok"]:
            backup_path.unlink(missing_ok=True)
            raise LedgerOpsError("Backup failed post-copy verification; removed invalid backup artifact.")

        return {
            "schema_version": "ledger_ops_backup/v1",
            "ok": True,
            "database_path": str(resolved),
            "backup_path": str(backup_path),
            "backup_size_bytes": backup_path.stat().st_size,
            "backup_sha256": _sha256_file(backup_path),
            "pre_backup_verification": before,
            "post_backup_verification": after,
        }


def restore_ledger_database(
    *,
    backup_path: str,
    database_path: str | None = None,
    verify_source: bool = True,
    verify_after: bool = True,
    allow_overwrite: bool = False,
    pre_restore_backup_dir: str | None = None,
) -> dict[str, Any]:
    """Restore a SQLite ledger backup into the configured ledger path and verify it."""

    source = _ensure_not_symlinked(backup_path, label="LEDGER_RESTORE_BACKUP_PATH")
    _ensure_regular_file(source, label="LEDGER_RESTORE_BACKUP_PATH")

    with _with_database_path(database_path):
        destination = _database_path_for_operation(label="LEDGER_RESTORE_DESTINATION_PATH")
        if destination.exists() and not allow_overwrite:
            raise LedgerOpsError(
                f"Refusing to overwrite existing ledger database without allow_overwrite: {destination}"
            )

        source_verification = verify_ledger(database_path=str(source)) if verify_source else {"ok": True}
        if verify_source and not source_verification["ok"]:
            raise LedgerOpsError("Refusing to restore backup with failed source verification.")

        pre_restore_backup: dict[str, Any] | None = None
        if destination.exists():
            backup_directory = _ensure_not_symlinked(
                pre_restore_backup_dir if pre_restore_backup_dir else destination.parent / "pre-restore-backups",
                label="LEDGER_PRE_RESTORE_BACKUP_DIR",
            )
            _ensure_directory_path(backup_directory, label="LEDGER_PRE_RESTORE_BACKUP_DIR", create=True)
            preserved_path = backup_directory / f"{destination.stem}.pre-restore.{_timestamp_slug()}{destination.suffix}"
            shutil.copy2(destination, preserved_path)
            pre_restore_backup = {
                "schema_version": "ledger_ops_pre_restore_backup/v1",
                "ok": True,
                "path": str(preserved_path),
                "size_bytes": preserved_path.stat().st_size,
                "sha256": _sha256_file(preserved_path),
            }

        destination.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(source) as src, sqlite3.connect(destination) as dst:
            src.backup(dst)

        restored_verification = verify_ledger(database_path=str(destination)) if verify_after else {"ok": True}
        if verify_after and not restored_verification["ok"]:
            raise LedgerOpsError("Restored ledger failed post-restore verification.")

        return {
            "schema_version": "ledger_ops_restore/v1",
            "ok": True,
            "backup_path": str(source),
            "database_path": str(destination),
            "restored_size_bytes": destination.stat().st_size,
            "restored_sha256": _sha256_file(destination),
            "pre_restore_backup": pre_restore_backup,
            "source_verification": source_verification,
            "post_restore_verification": restored_verification,
        }


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify, back up, and restore the strategy-validator forensic ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    verify = sub.add_parser("verify", help="Verify ledger schema and hash-chain integrity")
    verify.add_argument("--database-path", default="", help="Explicit SQLite database path")
    verify.add_argument("--experiment-id", default="", help="Optionally verify one experiment stream")
    verify.add_argument("--json", action="store_true", help="Emit JSON")

    verify_integrity = sub.add_parser(
        "verify-integrity",
        help="Verify ledger schema/hash-chain and operator action journal as one JSON report",
    )
    verify_integrity.add_argument("--database-path", default="", help="Explicit SQLite database path")
    verify_integrity.add_argument("--experiment-id", default="", help="Optionally verify one experiment stream")
    verify_integrity.add_argument("--json", action="store_true", help="Emit JSON")

    operator_actions = sub.add_parser(
        "verify-operator-actions",
        help="Verify operator action event journal chain integrity",
    )
    operator_actions.add_argument("--database-path", default="", help="Explicit SQLite database path")
    operator_actions.add_argument("--json", action="store_true", help="Emit JSON")

    index_operator_actions = sub.add_parser(
        "index-operator-actions",
        help="Build a compact operator action event projection index",
    )
    index_operator_actions.add_argument("--database-path", default="", help="Explicit SQLite database path")
    index_operator_actions.add_argument("--output-path", default="", help="Optional JSON output path")
    index_operator_actions.add_argument("--json", action="store_true", help="Emit JSON")

    backup = sub.add_parser("backup", help="Create a verified SQLite backup")
    backup.add_argument("--database-path", default="", help="Explicit SQLite database path")
    backup.add_argument("--backup-dir", default="", help="Directory for timestamped backups")
    backup.add_argument("--no-pre-verify", action="store_true", help="Skip pre-backup hash-chain verification")
    backup.add_argument("--no-post-verify", action="store_true", help="Skip backup artifact verification")
    backup.add_argument("--json", action="store_true", help="Emit JSON")

    restore = sub.add_parser("restore", help="Restore a verified SQLite backup")
    restore.add_argument("--backup-path", required=True, help="SQLite backup path to restore")
    restore.add_argument("--database-path", default="", help="Destination SQLite database path")
    restore.add_argument("--allow-overwrite", action="store_true", help="Allow replacing an existing destination database")
    restore.add_argument("--pre-restore-backup-dir", default="", help="Directory where the displaced destination ledger is preserved before overwrite")
    restore.add_argument("--no-source-verify", action="store_true", help="Skip backup source verification")
    restore.add_argument("--no-post-verify", action="store_true", help="Skip restored database verification")
    restore.add_argument("--json", action="store_true", help="Emit JSON")

    ns = parser.parse_args(argv)
    try:
        if ns.command == "verify":
            payload = verify_ledger(database_path=ns.database_path or None, experiment_id=ns.experiment_id or None)
            _emit(payload, as_json=ns.json)
            return 0 if payload["ok"] else 1
        if ns.command == "verify-integrity":
            payload = verify_ledger_integrity(database_path=ns.database_path or None, experiment_id=ns.experiment_id or None)
            _emit(payload, as_json=ns.json)
            return 0 if payload["ok"] else 1
        if ns.command == "verify-operator-actions":
            payload = verify_operator_action_journal(database_path=ns.database_path or None)
            _emit(payload, as_json=ns.json)
            return 0 if payload["ok"] else 1
        if ns.command == "index-operator-actions":
            with _with_database_path(ns.database_path or None):
                resolved = resolve_database_path()
                index = build_operator_action_event_projection_index(database_path=resolved, readonly=True)
                if ns.output_path:
                    write_operator_action_event_projection_index(
                        Path(ns.output_path),
                        database_path=resolved,
                        index=index,
                        readonly=True,
                    )
                payload = index.to_payload()
            _emit(payload, as_json=ns.json)
            return 0 if payload["ok"] else 1
        if ns.command == "backup":
            payload = backup_ledger_database(
                database_path=ns.database_path or None,
                backup_dir=ns.backup_dir or None,
                verify_before=not ns.no_pre_verify,
                verify_after=not ns.no_post_verify,
            )
            _emit(payload, as_json=ns.json)
            return 0
        payload = restore_ledger_database(
            backup_path=ns.backup_path,
            database_path=ns.database_path or None,
            verify_source=not ns.no_source_verify,
            verify_after=not ns.no_post_verify,
            allow_overwrite=ns.allow_overwrite,
            pre_restore_backup_dir=ns.pre_restore_backup_dir or None,
        )
        _emit(payload, as_json=ns.json)
        return 0
    except LedgerOpsError as exc:
        payload = {"schema_version": "ledger_ops_error/v1", "ok": False, "error": str(exc)}
        _emit(payload, as_json=getattr(ns, "json", False))
        return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
