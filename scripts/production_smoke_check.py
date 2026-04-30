#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from strategy_validator.cli.ledger_ops import restore_ledger_database, verify_operator_action_journal
from strategy_validator.ledger._append_only import resolve_database_path
from strategy_validator.projections.operator_action_event_index import (
    build_operator_action_event_projection_index,
    write_operator_action_event_projection_index,
)
from strategy_validator.validator.readiness import perform_deployment_readiness_check, perform_readiness_check

_LEDGER_DB_ENV = "STRATEGY_VALIDATOR_LEDGER_DB_PATH"


def _to_jsonable(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def _with_optional_database_path(database_path: str):
    class _Ctx:
        def __enter__(self):
            self.previous = os.environ.get(_LEDGER_DB_ENV)
            if database_path:
                os.environ[_LEDGER_DB_ENV] = database_path
            return self

        def __exit__(self, exc_type, exc, tb):
            if database_path:
                if self.previous is None:
                    os.environ.pop(_LEDGER_DB_ENV, None)
                else:
                    os.environ[_LEDGER_DB_ENV] = self.previous
            return False

    return _Ctx()


def _operator_action_index_payload(*, database_path: str, output_path: str) -> dict[str, Any]:
    with _with_optional_database_path(database_path):
        resolved = Path(database_path) if database_path else resolve_database_path()
        index = build_operator_action_event_projection_index(database_path=resolved, readonly=True)
        if output_path:
            write_operator_action_event_projection_index(Path(output_path), database_path=resolved, index=index, readonly=True)
        return index.to_payload()


def _summary_status(payload: dict[str, Any]) -> tuple[bool, str]:
    if payload.get("schema_version") == "production_smoke_check_diagnostics/v1":
        return bool(payload.get("ok")), "PASS" if payload.get("ok") else "FAIL"
    status = payload.get("status") or payload.get("readiness", {}).get("status")
    return status == "READY", str(status or "UNKNOWN")


def _write_diagnostics_markdown(output_path: str, payload: dict[str, Any]) -> None:
    """Write a compact operator-facing Markdown summary for CI artifacts."""
    if not output_path:
        return
    ok, status = _summary_status(payload)
    readiness = payload.get("readiness", payload)
    checks = readiness.get("checks", {}) if isinstance(readiness, dict) else {}
    blockers = readiness.get("blockers", []) if isinstance(readiness, dict) else []
    warnings = readiness.get("warnings", []) if isinstance(readiness, dict) else []
    chain = payload.get("operator_action_chain") or {}
    index = payload.get("operator_action_index") or {}
    restore = payload.get("restore_drill") or {}
    lines = [
        "# Production smoke diagnostics",
        "",
        f"- Overall: {'PASS' if ok else 'FAIL'}",
        f"- Status: {status}",
        f"- Readiness status: {readiness.get('status', 'UNKNOWN') if isinstance(readiness, dict) else 'UNKNOWN'}",
        f"- Restore drill: {restore.get('ok') if restore else 'not run'}",
        f"- Operator action chain: {chain.get('ok') if chain else 'not run'}",
        f"- Operator action events indexed: {index.get('event_count') if index else 'not run'}",
        "",
        "## Readiness checks",
    ]
    if checks:
        for key in sorted(checks):
            lines.append(f"- `{key}`: `{checks[key]}`")
    else:
        lines.append("- no checks reported")
    lines.extend(["", "## Blockers"])
    if blockers:
        for blocker in blockers:
            code = blocker.get("code", "UNKNOWN") if isinstance(blocker, dict) else str(blocker)
            message = blocker.get("message", "") if isinstance(blocker, dict) else ""
            lines.append(f"- `{code}` {message}".rstrip())
    else:
        lines.append("- none")
    lines.extend(["", "## Warnings"])
    if warnings:
        for warning in warnings:
            code = warning.get("code", "UNKNOWN") if isinstance(warning, dict) else str(warning)
            message = warning.get("message", "") if isinstance(warning, dict) else ""
            lines.append(f"- `{code}` {message}".rstrip())
    else:
        lines.append("- none")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run production readiness smoke checks for strategy-validator.")
    parser.add_argument("--deployment-tier", action="store_true", help="Run broader deployment readiness checks, not only runtime readiness.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for deployment hygiene checks.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the selected readiness report is READY.")
    parser.add_argument("--restore-drill-backup-path", default="", help="Optional ledger backup path for a verified restore drill.")
    parser.add_argument("--restore-drill-database-path", default="", help="Destination path for the optional restore drill.")
    parser.add_argument("--restore-drill-allow-overwrite", action="store_true", help="Allow restore drill to overwrite the destination path.")
    parser.add_argument("--operator-ledger-database-path", default="", help="Optional ledger path for operator action chain/index diagnostics.")
    parser.add_argument("--verify-operator-action-chain", action="store_true", help="Include operator action journal hash-chain verification in the smoke payload.")
    parser.add_argument("--operator-action-index-output-path", default="", help="Optional path to materialize the operator action event projection index.")
    parser.add_argument("--summary-markdown-output-path", default="", help="Optional Markdown summary path for CI/operator diagnostics.")
    args = parser.parse_args(argv)

    if args.deployment_tier:
        report = perform_deployment_readiness_check(repo_root=Path(args.repo_root))
    else:
        report = perform_readiness_check()

    readiness_payload = _to_jsonable(report)
    payload: dict[str, Any] = readiness_payload

    restore_report: dict[str, Any] | None = None
    if args.restore_drill_backup_path:
        if not args.restore_drill_database_path:
            payload = {
                "schema_version": "production_smoke_check_error/v1",
                "ok": False,
                "error": "--restore-drill-database-path is required when --restore-drill-backup-path is set",
                "readiness": readiness_payload,
            }
            _write_diagnostics_markdown(args.summary_markdown_output_path, payload)
            print(json.dumps(payload, indent=2, sort_keys=True))
            return 2
        restore_report = restore_ledger_database(
            backup_path=args.restore_drill_backup_path,
            database_path=args.restore_drill_database_path,
            allow_overwrite=args.restore_drill_allow_overwrite,
        )

    operator_chain_report: dict[str, Any] | None = None
    if args.verify_operator_action_chain:
        operator_chain_report = verify_operator_action_journal(database_path=args.operator_ledger_database_path or None)

    operator_index_payload: dict[str, Any] | None = None
    if args.operator_action_index_output_path:
        operator_index_payload = _operator_action_index_payload(
            database_path=args.operator_ledger_database_path,
            output_path=args.operator_action_index_output_path,
        )

    if restore_report is not None or operator_chain_report is not None or operator_index_payload is not None:
        ok = readiness_payload.get("status") == "READY"
        if restore_report is not None:
            ok = ok and bool(restore_report.get("ok"))
        if operator_chain_report is not None:
            ok = ok and bool(operator_chain_report.get("ok"))
        if operator_index_payload is not None:
            ok = ok and bool(operator_index_payload.get("ok"))
        payload = {
            "schema_version": "production_smoke_check_diagnostics/v1",
            "ok": ok,
            "readiness": readiness_payload,
            "restore_drill": restore_report,
            "operator_action_chain": operator_chain_report,
            "operator_action_index": operator_index_payload,
        }

    _write_diagnostics_markdown(args.summary_markdown_output_path, payload)
    print(json.dumps(payload, indent=2, sort_keys=True))
    status = payload.get("status") or payload.get("readiness", {}).get("status")
    if args.require_ready and status != "READY":
        return 2
    if payload.get("schema_version") == "production_smoke_check_diagnostics/v1" and not payload.get("ok"):
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
