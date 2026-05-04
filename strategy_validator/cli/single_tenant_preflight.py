"""Single-tenant backend deployment preflight.

This command is intentionally backend-only.  It prepares/verifies the local
SQLite ledger, backup directory, artifact root, production token contract, and
optional backup/restore drill used by the single-tenant container envelope.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.core.token_policy import (
    REQUIRED_MUTATION_SCOPES,
    is_placeholder_token,
    missing_required_mutation_scopes,
    split_token_scopes,
)

from strategy_validator.validator.readiness import perform_deployment_readiness_check
from strategy_validator.cli.ledger_ops import (
    LedgerOpsError,
    backup_ledger_database,
    restore_ledger_database,
    verify_ledger,
    verify_operator_action_journal,
)
from strategy_validator.cli.migrate import run_migration
from strategy_validator.cli.deployment_env_check import (
    absolute_path_preserving_symlink,
    symlink_components_preserving_path,
)
from strategy_validator.ledger._append_only import resolve_database_path

_ENV_MODE = "STRATEGY_VALIDATOR_MODE"
_ENV_API_TOKEN = "STRATEGY_VALIDATOR_API_TOKEN"
_ENV_API_TOKEN_SCOPES = "STRATEGY_VALIDATOR_API_TOKEN_SCOPES"
_ENV_RESEARCH_API_TOKEN = "STRATEGY_VALIDATOR_RESEARCH_API_TOKEN"
_ENV_LEDGER_DB_PATH = "STRATEGY_VALIDATOR_LEDGER_DB_PATH"
_ENV_LEDGER_BACKUP_DIR = "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR"
_ENV_ARTIFACT_ROOT = "STRATEGY_VALIDATOR_ARTIFACT_ROOT"
_FRONTEND_PACKAGE_PATH = "ui/strategist-web"
_REQUIRED_MUTATION_SCOPES = REQUIRED_MUTATION_SCOPES
# Required production scopes: operator:command:write, operator:projection:read
@contextmanager
def _temporary_env(overrides: dict[str, str | None]):
    previous = {name: os.environ.get(name) for name in overrides}
    try:
        for name, value in overrides.items():
            if value is None:
                continue
            os.environ[name] = value
        yield
    finally:
        for name, value in previous.items():
            if value is None:
                os.environ.pop(name, None)
            else:
                os.environ[name] = value


def _path_value(explicit: str, env_name: str, fallback: Path) -> Path:
    if explicit:
        return absolute_path_preserving_symlink(explicit)
    raw = os.environ.get(env_name, "").strip()
    if raw:
        return absolute_path_preserving_symlink(raw)
    return absolute_path_preserving_symlink(fallback)


def _symlink_components(path: Path) -> tuple[str, ...]:
    """Return symlink components in a durable deployment path."""

    return tuple(str(candidate) for candidate in symlink_components_preserving_path(path))


def _durable_path_integrity(*, db_path: Path, backup_path: Path, artifact_path: Path, restore_drill_path: Path | None) -> dict[str, Any]:
    entries = {
        "ledger_database_path": db_path,
        "ledger_backup_dir": backup_path,
        "artifact_root": artifact_path,
    }
    if restore_drill_path is not None:
        entries["restore_drill_path"] = restore_drill_path

    details: dict[str, Any] = {}
    errors: list[str] = []
    for name, path in entries.items():
        symlinks = _symlink_components(path)
        details[name] = {
            "path": str(path),
            "symlink_components": list(symlinks),
            "ok": not symlinks,
        }
        if symlinks:
            errors.append(f"{name}: SYMLINK_IN_DURABLE_PATH: {', '.join(symlinks)}")
    return {"ok": not errors, "paths": details, "errors": errors}


def _ensure_writable_dir(path: Path, *, prepare: bool) -> dict[str, Any]:
    if prepare:
        path.mkdir(parents=True, exist_ok=True)
    exists = path.exists()
    is_dir = path.is_dir() if exists else False
    writable = os.access(path, os.W_OK) if is_dir else False
    return {
        "path": str(path),
        "exists": exists,
        "is_dir": is_dir,
        "writable": writable,
        "ok": exists and is_dir and writable,
    }


def _frontend_status(repo_root: Path) -> dict[str, Any]:
    package_json = repo_root / _FRONTEND_PACKAGE_PATH / "package.json"
    return {
        "expected_package": _FRONTEND_PACKAGE_PATH,
        "package_json_exists": package_json.exists(),
        "frontend_readiness_claimed": False,
        "readiness_claimed": False,
        "status": "present" if package_json.exists() else "absent",
    }


def build_single_tenant_deployment_preflight(
    *,
    repo_root: str | Path = ".",
    database_path: str = "",
    backup_dir: str = "",
    artifact_root: str = "",
    prepare: bool = False,
    verify_backup_restore: bool = False,
    restore_drill_path: str = "",
) -> dict[str, Any]:
    """Return the single-tenant backend deployment preflight payload.

    `prepare=True` is intentionally explicit: without it the command only
    verifies existing state and refuses to create deployment directories or a
    ledger DB.  This keeps CI/ops evidence honest while still allowing a local
    bootstrap path for a fresh single-tenant volume.
    """

    repo = Path(repo_root).resolve()
    default_db = Path(os.environ.get(_ENV_LEDGER_DB_PATH, "./var/strategy-validator/ledger.sqlite3"))
    db_path = _path_value(database_path, _ENV_LEDGER_DB_PATH, default_db)
    backup_path = _path_value(backup_dir, _ENV_LEDGER_BACKUP_DIR, db_path.parent / "backups")
    artifact_path = _path_value(artifact_root, _ENV_ARTIFACT_ROOT, db_path.parent / "artifacts")
    restore_drill = absolute_path_preserving_symlink(restore_drill_path) if restore_drill_path else None
    path_integrity = _durable_path_integrity(
        db_path=db_path,
        backup_path=backup_path,
        artifact_path=artifact_path,
        restore_drill_path=restore_drill,
    )

    env_overrides = {
        _ENV_LEDGER_DB_PATH: str(db_path),
        _ENV_LEDGER_BACKUP_DIR: str(backup_path),
        _ENV_ARTIFACT_ROOT: str(artifact_path),
    }

    preparation: dict[str, Any] = {
        "prepared": bool(prepare),
        "migration": None,
        "backup_dir": None,
        "artifact_root": None,
        "path_integrity": path_integrity,
    }
    backup_restore: dict[str, Any] | None = None
    ledger_verification: dict[str, Any] | None = None
    operator_action_chain: dict[str, Any] | None = None
    errors: list[str] = list(path_integrity["errors"])

    with _temporary_env(env_overrides):
        if not path_integrity["ok"]:
            preparation["backup_dir"] = {"path": str(backup_path), "exists": backup_path.exists(), "is_dir": False, "writable": False, "ok": False}
            preparation["artifact_root"] = {"path": str(artifact_path), "exists": artifact_path.exists(), "is_dir": False, "writable": False, "ok": False}
            ledger_verification = {
                "schema_version": "ledger_ops_verify/v1",
                "ok": False,
                "database_path": str(db_path),
                "database_exists": db_path.exists(),
                "error": "skipped because durable deployment path integrity failed",
            }
            operator_action_chain = {
                "schema_version": "ledger_ops_operator_action_chain_verify/v1",
                "ok": False,
                "database_path": str(db_path),
                "database_exists": db_path.exists(),
                "issues": ["skipped because durable deployment path integrity failed"],
            }
            backup_restore = (
                {
                    "schema_version": "single_tenant_backup_restore_drill/v1",
                    "ok": False,
                    "error": "skipped because durable deployment path integrity failed",
                }
                if verify_backup_restore
                else None
            )
            deployment = {
                "status": "BLOCKED",
                "skipped": True,
                "reason": "durable deployment path integrity failed",
            }
        else:
            if prepare:
                db_path.parent.mkdir(parents=True, exist_ok=True)
                backup_path.mkdir(parents=True, exist_ok=True)
                artifact_path.mkdir(parents=True, exist_ok=True)
                preparation["migration"] = run_migration(database_path=str(db_path))

            preparation["backup_dir"] = _ensure_writable_dir(backup_path, prepare=prepare)
            preparation["artifact_root"] = _ensure_writable_dir(artifact_path, prepare=prepare)

            try:
                ledger_verification = verify_ledger(database_path=str(db_path))
            except Exception as exc:  # pragma: no cover - defensive operator diagnostic.
                errors.append(f"ledger verification failed: {exc}")
                ledger_verification = {"ok": False, "error": str(exc), "database_path": str(db_path)}

            try:
                operator_action_chain = verify_operator_action_journal(database_path=str(db_path))
            except Exception as exc:  # pragma: no cover - defensive operator diagnostic.
                errors.append(f"operator action journal verification failed: {exc}")
                operator_action_chain = {"ok": False, "error": str(exc), "database_path": str(db_path)}

            if verify_backup_restore:
                try:
                    backup_report = backup_ledger_database(database_path=str(db_path), backup_dir=str(backup_path))
                    restore_path = restore_drill if restore_drill is not None else backup_path / "restore-drill.sqlite3"
                    restore_report = restore_ledger_database(
                        backup_path=str(backup_report["backup_path"]),
                        database_path=str(restore_path),
                        allow_overwrite=True,
                    )
                    backup_restore = {
                        "schema_version": "single_tenant_backup_restore_drill/v1",
                        "ok": bool(backup_report.get("ok") and restore_report.get("ok")),
                        "backup": backup_report,
                        "restore": restore_report,
                    }
                except LedgerOpsError as exc:
                    backup_restore = {
                        "schema_version": "single_tenant_backup_restore_drill/v1",
                        "ok": False,
                        "error": str(exc),
                    }
                    errors.append(f"backup/restore drill failed: {exc}")

            deployment_report = perform_deployment_readiness_check(repo_root=repo)
            deployment = deployment_report.model_dump(mode="json") if hasattr(deployment_report, "model_dump") else deployment_report.dict()

    token = os.environ.get(_ENV_API_TOKEN, "").strip()
    scopes = split_token_scopes(
        os.environ.get(_ENV_API_TOKEN_SCOPES, ""),
        default_when_empty=os.environ.get(_ENV_MODE, "").strip().upper() != "PRODUCTION",
    )
    missing_scopes = list(missing_required_mutation_scopes(scopes))
    token_configured = bool(token)
    token_placeholder = is_placeholder_token(token)
    env_contract = {
        "mode": os.environ.get(_ENV_MODE, "").strip() or None,
        "mode_is_production": os.environ.get(_ENV_MODE, "").strip().upper() == "PRODUCTION",
        "api_token_configured": token_configured,
        "api_token_not_placeholder": token_configured and not token_placeholder,
        "api_token_scope_count": len(scopes),
        "api_token_required_scopes_present": not missing_scopes,
        "api_token_missing_required_scopes": missing_scopes,
        "research_api_token_configured": bool(os.environ.get(_ENV_RESEARCH_API_TOKEN, "").strip()),
        "ledger_database_path": str(db_path),
        "ledger_backup_dir": str(backup_path),
        "artifact_root": str(artifact_path),
    }

    checks = {
        "backend_only_single_tenant_scope": True,
        "deployment_paths_not_symlinked": bool(path_integrity["ok"]),
        "production_mode": bool(env_contract["mode_is_production"]),
        "api_token_configured": bool(env_contract["api_token_configured"]),
        "api_token_not_placeholder": bool(env_contract["api_token_not_placeholder"]),
        "api_token_required_scopes_present": bool(env_contract["api_token_required_scopes_present"]),
        "ledger_database_verified": bool(ledger_verification and ledger_verification.get("ok")),
        "operator_action_journal_verified": bool(operator_action_chain and operator_action_chain.get("ok")),
        "backup_dir_writable": bool(preparation["backup_dir"] and preparation["backup_dir"].get("ok")),
        "artifact_root_writable": bool(preparation["artifact_root"] and preparation["artifact_root"].get("ok")),
        "deployment_readiness_ready": deployment.get("status") == "READY",
        "backup_restore_drill_ok": True if not verify_backup_restore else bool(backup_restore and backup_restore.get("ok")),
        "frontend_readiness_not_claimed": _frontend_status(repo)["readiness_claimed"] is False,
    }
    ok = all(checks.values()) and not errors
    recommended_action = "DEPLOY_SINGLE_TENANT_BACKEND" if ok else "BLOCK_DEPLOYMENT_AND_FIX_PREFLIGHT"

    return {
        "schema_version": "single_tenant_deployment_preflight/v1",
        "ok": ok,
        "deployment_model": "single_tenant_backend_only",
        "recommended_action": recommended_action,
        "repo_root": str(repo),
        "environment": env_contract,
        "frontend": _frontend_status(repo),
        "checks": checks,
        "preparation": preparation,
        "deployment_readiness": deployment,
        "ledger_verification": ledger_verification,
        "operator_action_chain": operator_action_chain,
        "backup_restore_drill": backup_restore,
        "errors": errors,
    }


def _write_summary(path: str, payload: dict[str, Any]) -> None:
    if not path:
        return
    target = absolute_path_preserving_symlink(path)
    symlinks = symlink_components_preserving_path(target)
    if symlinks:
        payload["ok"] = False
        payload["recommended_action"] = "BLOCK_DEPLOYMENT_AND_FIX_PREFLIGHT"
        payload.setdefault("errors", []).append(
            "summary_markdown_output_path: SYMLINK_IN_OUTPUT_PATH: "
            + ", ".join(str(item) for item in symlinks)
        )
        payload.setdefault("checks", {})["summary_markdown_output_path_not_symlinked"] = False
        return
    target.parent.mkdir(parents=True, exist_ok=True)
    checks = payload.get("checks", {})
    lines = [
        "# Single-tenant deployment preflight",
        "",
        f"- Overall: {'PASS' if payload.get('ok') else 'FAIL'}",
        f"- Recommended action: `{payload.get('recommended_action')}`",
        f"- Deployment model: `{payload.get('deployment_model')}`",
        f"- Ledger: `{payload.get('environment', {}).get('ledger_database_path')}`",
        f"- Backup dir: `{payload.get('environment', {}).get('ledger_backup_dir')}`",
        f"- Artifact root: `{payload.get('environment', {}).get('artifact_root')}`",
        "",
        "## Checks",
    ]
    for key in sorted(checks):
        lines.append(f"- `{key}`: `{checks[key]}`")
    errors = payload.get("errors") or []
    if errors:
        lines.extend(["", "## Errors"])
        lines.extend(f"- {error}" for error in errors)
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Prepare and verify a single-tenant backend deployment envelope.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for private-key and frontend readiness checks.")
    parser.add_argument("--database-path", default="", help="Explicit SQLite ledger path.")
    parser.add_argument("--backup-dir", default="", help="Writable backup directory.")
    parser.add_argument("--artifact-root", default="", help="Writable artifact root.")
    parser.add_argument("--prepare", action="store_true", help="Create directories and run ledger migrations before checking readiness.")
    parser.add_argument("--verify-backup-restore", action="store_true", help="Create a verified backup and restore it to a drill destination.")
    parser.add_argument("--restore-drill-path", default="", help="Optional destination path for restore drill output.")
    parser.add_argument("--summary-markdown-output-path", default="", help="Optional operator Markdown summary path.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON as well for stable machine parsing.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the full single-tenant preflight passes.")
    ns = parser.parse_args(argv)

    payload = build_single_tenant_deployment_preflight(
        repo_root=ns.repo_root,
        database_path=ns.database_path,
        backup_dir=ns.backup_dir,
        artifact_root=ns.artifact_root,
        prepare=ns.prepare,
        verify_backup_restore=ns.verify_backup_restore,
        restore_drill_path=ns.restore_drill_path,
    )
    _write_summary(ns.summary_markdown_output_path, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    sys.stdout.flush()
    return 2 if ns.require_ready and not payload["ok"] else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
