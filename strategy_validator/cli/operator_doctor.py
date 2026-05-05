"""Read-only single-tenant operator diagnostic command."""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.cli.deployment_env_check import (
    build_single_tenant_deployment_env_check,
    parse_env_file,
)
from strategy_validator.cli.single_tenant_api_smoke import (
    build_single_tenant_api_smoke,
    resolve_smoke_base_url,
    resolve_smoke_token,
)
from strategy_validator.migrations import EXPECTED_SCHEMA_VERSION, get_current_schema_version

_SCHEMA_VERSION = "operator_doctor/v1"
_SENSITIVE_PATTERNS = ("TOKEN", "KEY", "API_KEY", "API-KEY", "SECRET", "PASSWORD", "BEARER")
_SENSITIVE_TEXT_PATTERN = re.compile(r"(?i)(api[_-]?key|token|secret|password|bearer)")
_PROVIDER_ENV_KEYS = (
    "APCA_API_KEY_ID",
    "APCA_API_SECRET_KEY",
    "ALPHA_VANTAGE_API_KEY",
    "POLYGON_API_KEY",
    "FMP_API_KEY",
    "MASSIVE_API_KEY",
    "NEWSAPI_API_KEY",
    "TIINGO_API_KEY",
    "SIMFIN_API_KEY",
    "NVIDIA_NIM_API_KEY",
)
_DISCALIMERS = (
    "Local diagnostic only.",
    "Not production deployment approval.",
    "Not operator signoff.",
    "No live trading authorization.",
    "No profitability claim.",
)


@dataclass(frozen=True)
class DoctorStatus:
    status: str
    detail: str

    def to_payload(self) -> dict[str, str]:
        return {"status": self.status, "detail": self.detail}


def _redact_key_value(key: str, value: str) -> str:
    upper = key.upper()
    if any(item in upper for item in _SENSITIVE_PATTERNS):
        return "<redacted>"
    return value


def _redact_text(value: str) -> str:
    if _SENSITIVE_TEXT_PATTERN.search(value):
        return "<redacted>"
    return value


def _safe_detail(text: str, *, limit: int = 280) -> str:
    text = _redact_text(text)
    return text if len(text) <= limit else text[: limit - 3] + "..."


def _provider_key_posture(env_values: dict[str, str]) -> DoctorStatus:
    configured = [key for key in _PROVIDER_ENV_KEYS if env_values.get(key, "").strip()]
    if configured:
        return DoctorStatus("OPTIONAL_KEYS_PRESENT", f"{len(configured)} optional provider key(s) configured.")
    return DoctorStatus(
        "PENDING_KEY",
        "Optional provider keys are not configured. Local diagnostics can continue without them.",
    )


def _migration_status(db_path_text: str) -> DoctorStatus:
    db_path = Path(db_path_text.strip()) if db_path_text.strip() else None
    if db_path is None:
        return DoctorStatus("UNKNOWN", "ledger database path is not set.")
    if not db_path.exists():
        return DoctorStatus("MISSING", f"ledger database does not exist at {db_path}.")
    if not db_path.is_file():
        return DoctorStatus("FAIL", f"ledger database path is not a regular file: {db_path}.")
    try:
        with sqlite3.connect(db_path) as connection:
            current = get_current_schema_version(connection)
    except Exception as exc:  # pragma: no cover - defensive diagnostics.
        return DoctorStatus("FAIL", f"could not read ledger schema version: {type(exc).__name__}: {_safe_detail(str(exc))}")
    if current == EXPECTED_SCHEMA_VERSION:
        return DoctorStatus("CURRENT", f"schema version is current at {current}.")
    if current < EXPECTED_SCHEMA_VERSION:
        return DoctorStatus("OUTDATED", f"schema version {current} is behind expected {EXPECTED_SCHEMA_VERSION}.")
    return DoctorStatus("UNKNOWN", f"schema version {current} is ahead of expected {EXPECTED_SCHEMA_VERSION}.")


def _path_status(path_text: str, label: str) -> DoctorStatus:
    value = path_text.strip()
    if not value:
        return DoctorStatus("MISSING", f"{label} is not configured.")
    candidate = Path(value)
    if candidate.exists():
        return DoctorStatus("OK", f"{label} exists at {candidate}.")
    return DoctorStatus("MISSING", f"{label} does not exist at {candidate}.")


def _run_mode_status(env_values: dict[str, str]) -> DoctorStatus:
    mode = env_values.get("STRATEGY_VALIDATOR_MODE", "").strip().upper()
    if not mode:
        return DoctorStatus("UNKNOWN", "STRATEGY_VALIDATOR_MODE is not set.")
    if mode != "PRODUCTION":
        return DoctorStatus("WARN", f"run mode is {mode}, expected PRODUCTION for single-tenant readiness.")
    return DoctorStatus("OK", "run mode is PRODUCTION.")


def _env_file_status(env_file: Path) -> DoctorStatus:
    if not env_file.exists():
        return DoctorStatus("MISSING", f"env file does not exist: {env_file}.")
    if not env_file.is_file():
        return DoctorStatus("FAIL", f"env path is not a regular file: {env_file}.")
    return DoctorStatus("OK", f"env file exists: {env_file}.")


def _deployment_env_status(env_file: Path) -> tuple[DoctorStatus, dict[str, Any] | None]:
    if not env_file.exists() or not env_file.is_file():
        return DoctorStatus("MISSING", "deployment env check skipped because env file is missing."), None
    report = build_single_tenant_deployment_env_check(env_file)
    payload = report.to_payload()
    if report.ok:
        return DoctorStatus("PASS", "deployment env check passed."), payload
    return DoctorStatus("FAIL", f"deployment env check failed with {report.issue_count} error(s)."), payload


def _api_smoke_status(
    *,
    include_api_smoke: bool,
    base_url: str,
    token_source: str,
    token: str,
    token_env_var: str,
    env_file: Path | None,
    operator_id: str,
) -> DoctorStatus:
    if not include_api_smoke:
        return DoctorStatus("NOT_RUN", "API smoke not requested. Use --include-api-smoke to run it.")
    try:
        resolved_base = resolve_smoke_base_url(base_url=base_url or None, env_file=env_file)
        resolution = resolve_smoke_token(
            token=token or None,
            token_env_var=token_env_var,
            env_file=env_file,
            token_source=token_source,  # type: ignore[arg-type]
        )
        report = build_single_tenant_api_smoke(base_url=resolved_base, token=resolution.token, operator_id=operator_id)
    except Exception as exc:
        return DoctorStatus("FAIL", f"API smoke failed to start: {type(exc).__name__}: {_safe_detail(str(exc))}")
    if report.ok:
        return DoctorStatus("PASS", "API smoke checks passed.")
    return DoctorStatus("FAIL", f"API smoke failed with {report.failed_step_count} failing step(s).")


def _release_verification_hint(repo_root: Path) -> DoctorStatus:
    json_path = repo_root / "artifacts" / "release_verification" / "latest" / "main-release-verification-pack.json"
    if json_path.exists():
        return DoctorStatus("FOUND", f"release verification evidence found at {json_path}.")
    return DoctorStatus("MISSING", "release verification evidence not found under artifacts/release_verification/latest.")


def _branch_audit_hint(repo_root: Path) -> DoctorStatus:
    json_path = repo_root / "artifacts" / "release_verification" / "latest" / "branch-cleanup-audit.json"
    if json_path.exists():
        return DoctorStatus("FOUND", f"branch cleanup audit found at {json_path}.")
    return DoctorStatus("MISSING", "branch cleanup audit not found under artifacts/release_verification/latest.")


def _canonical_status(status: str) -> str:
    normalized = (status or "UNKNOWN").upper()
    if normalized == "PASS":
        return "OK"
    if normalized == "WARN":
        return "WARN"
    if normalized == "FAIL":
        return "BLOCKED"
    return "UNKNOWN"


def build_operator_doctor_report(
    *,
    repo_root: str | Path = ".",
    env_file: str | Path = "deployment.env",
    include_api_smoke: bool = False,
    base_url: str = "",
    token_source: str = "auto",
    token: str = "",
    operator_id: str = "operator-doctor",
    token_env_var: str = "STRATEGY_VALIDATOR_API_TOKEN",
) -> dict[str, Any]:
    root = Path(repo_root).resolve()
    env_path = Path(env_file) if Path(env_file).is_absolute() else root / Path(env_file)
    file_status = _env_file_status(env_path)
    deployment_status, deployment_payload = _deployment_env_status(env_path)

    parsed_values: dict[str, str] = {}
    if env_path.exists() and env_path.is_file():
        parsed_values, _issues = parse_env_file(env_path)
    run_mode = _run_mode_status(parsed_values)
    provider_posture = _provider_key_posture(parsed_values)
    ledger_status = _path_status(parsed_values.get("STRATEGY_VALIDATOR_LEDGER_DB_PATH", ""), "ledger path")
    artifact_status = _path_status(parsed_values.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", ""), "artifact root")
    backup_status = _path_status(parsed_values.get("STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR", ""), "backup directory")
    migration_status = _migration_status(parsed_values.get("STRATEGY_VALIDATOR_LEDGER_DB_PATH", ""))
    release_hint = _release_verification_hint(root)
    branch_hint = _branch_audit_hint(root)
    api_smoke = _api_smoke_status(
        include_api_smoke=include_api_smoke,
        base_url=base_url,
        token_source=token_source,
        token=token,
        token_env_var=token_env_var,
        env_file=env_path if env_path.exists() else None,
        operator_id=operator_id,
    )

    blockers: list[str] = []
    warnings: list[str] = []
    recommendations: list[str] = []

    if file_status.status != "OK":
        blockers.append(file_status.detail)
        recommendations.append("python scripts/setup_local_deployment.py --force")
        recommendations.append("See docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md")
    if deployment_status.status == "FAIL":
        blockers.append(deployment_status.detail)
        recommendations.append("strategy-validator-deployment-env-check deployment.env --require-valid --json")
    if run_mode.status != "OK":
        blockers.append(run_mode.detail)
        recommendations.append("Set STRATEGY_VALIDATOR_MODE=PRODUCTION in deployment.env")
    if deployment_payload:
        values = deployment_payload.get("values", {})
        if isinstance(values, dict):
            if bool(values.get("api_token_placeholder_like")):
                blockers.append("Mutation API token is missing or placeholder-like.")
                recommendations.append("Rotate STRATEGY_VALIDATOR_API_TOKEN and re-run deployment env check")
            missing_scopes = values.get("api_token_missing_required_scopes", [])
            if isinstance(missing_scopes, list) and missing_scopes:
                blockers.append("Required mutation scopes are missing.")
                recommendations.append("Set STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read")
    if ledger_status.status != "OK":
        warnings.append(ledger_status.detail)
        recommendations.append("strategy-validator-single-tenant-preflight --prepare --require-ready --json")
    if migration_status.status in {"MISSING", "OUTDATED", "FAIL"}:
        warnings.append(migration_status.detail)
        recommendations.append("strategy-validator-migrate --json")
    if api_smoke.status == "NOT_RUN":
        recommendations.append("strategy-validator-single-tenant-api-smoke --env-file deployment.env --token-source env-file --require-pass --json")
    if release_hint.status == "MISSING":
        recommendations.append(
            "python scripts/main_release_verification_pack.py --output-dir artifacts/release_verification/latest --json --require-pass"
        )
    if branch_hint.status == "MISSING":
        recommendations.append(
            "python scripts/branch_cleanup_audit.py --json --output-json-path artifacts/release_verification/latest/branch-cleanup-audit.json"
        )
    if provider_posture.status == "PENDING_KEY":
        warnings.append(provider_posture.detail)

    dedup_recommendations = list(dict.fromkeys(recommendations))
    status = "PASS"
    if blockers:
        status = "FAIL"
    elif warnings:
        status = "WARN"

    payload = {
        "schema_version": _SCHEMA_VERSION,
        "ok": status == "PASS",
        "status": status,
        "canonical_status": _canonical_status(status),
        "run_mode": run_mode.to_payload(),
        "env_file_status": file_status.to_payload(),
        "deployment_env_status": deployment_status.to_payload(),
        "ledger_path_status": ledger_status.to_payload(),
        "artifact_root_status": artifact_status.to_payload(),
        "backup_dir_status": backup_status.to_payload(),
        "migration_status": migration_status.to_payload(),
        "release_verification_hint": release_hint.to_payload(),
        "branch_audit_hint": branch_hint.to_payload(),
        "provider_key_posture": provider_posture.to_payload(),
        "frontend_hint": {
            "status": "BACKEND_ONLY",
            "detail": "Frontend/cockpit readiness is separate and not implied by local backend diagnostics.",
        },
        "api_smoke_status": api_smoke.to_payload(),
        "next_recommended_commands": dedup_recommendations,
        "blockers": [_safe_detail(item) for item in blockers],
        "warnings": [_safe_detail(item) for item in warnings],
        "disclaimers": list(_DISCALIMERS),
        "environment_snapshot_redacted": {
            key: _redact_key_value(key, value)
            for key, value in sorted(parsed_values.items())
            if key.startswith("STRATEGY_VALIDATOR_") or key in _PROVIDER_ENV_KEYS
        },
        "token_source": token_source,
        "token_supplied": bool(token),
    }
    return payload


def write_markdown(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    text = [
        "# Operator Doctor Summary",
        "",
        f"- Status: `{payload.get('status', 'UNKNOWN')}`",
        f"- Ok: `{payload.get('ok', False)}`",
        "",
        "## Disclaimers",
        "",
    ]
    for line in payload.get("disclaimers", []):
        text.append(f"- {line}")
    text.extend(["", "## Next Recommended Commands", ""])
    for command in payload.get("next_recommended_commands", []):
        text.append(f"- `{_safe_detail(str(command))}`")
    text.extend(["", "## Blockers", ""])
    blockers = payload.get("blockers", [])
    if blockers:
        for item in blockers:
            text.append(f"- {_safe_detail(str(item))}")
    else:
        text.append("- None.")
    text.extend(["", "## Warnings", ""])
    warnings = payload.get("warnings", [])
    if warnings:
        for item in warnings:
            text.append(f"- {_safe_detail(str(item))}")
    else:
        text.append("- None.")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(text) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only single-tenant operator diagnostic command.")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--env-file", default="deployment.env")
    parser.add_argument("--include-api-smoke", action="store_true")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--token-source", choices=["auto", "env", "env-file", "explicit"], default="auto")
    parser.add_argument("--token", default="")
    parser.add_argument("--operator-id", default="operator-doctor")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--summary-markdown-output-path", default="")
    parser.add_argument("--require-ready", action="store_true")
    args = parser.parse_args(argv)

    token_source = args.token_source
    token = args.token
    if token_source == "explicit":
        token_source = "auto"
        token = token or os.environ.get("STRATEGY_VALIDATOR_API_TOKEN", "")

    payload = build_operator_doctor_report(
        repo_root=args.repo_root,
        env_file=args.env_file,
        include_api_smoke=args.include_api_smoke,
        base_url=args.base_url,
        token_source=token_source,
        token=token,
        operator_id=args.operator_id,
    )
    if args.summary_markdown_output_path:
        write_markdown(args.summary_markdown_output_path, payload)
    if args.json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            f"operator_doctor: {payload['status']}\n"
            f"blockers={len(payload['blockers'])} warnings={len(payload['warnings'])}\n"
        )
        for command in payload["next_recommended_commands"]:
            sys.stdout.write(f"- {command}\n")
    if args.require_ready and not payload["ok"]:
        return 2
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
