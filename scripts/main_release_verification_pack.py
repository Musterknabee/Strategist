#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "release_verification" / "latest"
SENSITIVE_ENV_KEYS = ("TOKEN", "KEY", "SECRET", "PASSWORD", "BEARER")
SAFE_ENV_KEYS = ("STRATEGY_VALIDATOR_MODE", "STRATEGY_VALIDATOR_HOST_PORT", "PYTHONPATH")
SENSITIVE_TEXT_MARKERS = ("token", "key", "secret", "password", "bearer")
DISCLOSURE_DISCLAIMERS = (
    "Local verification only.",
    "Not production deployment approval.",
    "Not operator signoff.",
    "Not live trading authorization.",
    "Not profitability evidence.",
)


@dataclass(frozen=True)
class GateResult:
    name: str
    command: str
    cwd: str
    exit_code: int
    duration_seconds: float
    status: str
    stdout_tail: str
    stderr_tail: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _tail(value: str, limit: int = 4000) -> str:
    return value[-limit:] if len(value) > limit else value


def _redact_text(value: str) -> str:
    redacted = value
    for marker in SENSITIVE_TEXT_MARKERS:
        redacted = re.sub(
            rf"(?i)\b({marker})(\s*[:=]\s*)([^\s,'\"`]+)",
            r"\1\2<redacted>",
            redacted,
        )
        redacted = re.sub(
            rf"(?i)(--?[A-Za-z0-9_-]*{marker}[A-Za-z0-9_-]*)(\s+)([^\s,'\"`]+)",
            r"\1\2<redacted>",
            redacted,
        )
    redacted = re.sub(r"(?i)\b(bearer)\s+([A-Za-z0-9._\-~+/=]+)", r"\1 <redacted>", redacted)
    return redacted


def _redacted_command(command: list[str]) -> str:
    return _redact_text(" ".join(command))


def redacted_environment_snapshot(env: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key in sorted(env):
        value = env[key]
        if any(marker in key.upper() for marker in SENSITIVE_ENV_KEYS):
            redacted[key] = "<redacted>"
        elif key in SAFE_ENV_KEYS:
            redacted[key] = value
        elif key.startswith("STRATEGY_VALIDATOR_") or key.startswith("GITHUB_") or key.startswith("CI"):
            redacted[key] = _redact_text(value)
    return redacted


def _run_gate(name: str, command: list[str], *, cwd: Path) -> GateResult:
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed_ms = int((time.perf_counter() - started) * 1000)
    code = int(proc.returncode)
    return GateResult(
        name=name,
        command=_redacted_command(command),
        cwd=str(cwd),
        exit_code=code,
        duration_seconds=round(elapsed_ms / 1000.0, 3),
        status="PASS" if code == 0 else "FAIL",
        stdout_tail=_redact_text(_tail(proc.stdout or "")),
        stderr_tail=_redact_text(_tail(proc.stderr or "")),
    )


def _backend_commands(python_exe: str, include_full_pytest: bool) -> list[tuple[str, list[str]]]:
    commands: list[tuple[str, list[str]]] = [
        ("source_health", [python_exe, "scripts/source_health.py"]),
        ("repository_truth_check", [python_exe, "scripts/repository_truth_check.py"]),
        ("migration_truth_check", [python_exe, "scripts/migration_truth_check.py"]),
        ("package_repo_check", [python_exe, "scripts/package_repo.py", "--check"]),
        ("ui_facade_snapshot_check", [python_exe, "scripts/ui_facade_contract_snapshot.py", "--check", "--no-static-fallback"]),
        ("openapi_snapshot_check", [python_exe, "scripts/openapi_contract_snapshot.py", "--check"]),
        ("frontend_ui_contract_check", [python_exe, "scripts/frontend_ui_contract_check.py"]),
        ("pytest_constitutional", [python_exe, "-m", "pytest", "tests/constitutional", "-q"]),
        ("pytest_api", [python_exe, "-m", "pytest", "tests/api", "-q"]),
        ("pytest_application", [python_exe, "-m", "pytest", "tests/application", "-q"]),
    ]
    if include_full_pytest:
        commands.append(("pytest_full", [python_exe, "-m", "pytest", "-q"]))
    return commands


def _frontend_commands() -> list[tuple[str, list[str], Path]]:
    web = REPO_ROOT / "ui" / "strategist-web"
    return [("npm_certify", ["npm", "run", "certify"], web)]


def _git_branch() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return (proc.stdout or "").strip() or "UNKNOWN"


def _git_head_sha() -> str:
    proc = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return (proc.stdout or "").strip() or "UNKNOWN"


def _dirty_tree_status() -> str:
    proc = subprocess.run(
        ["git", "status", "--porcelain"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        return "UNKNOWN"
    return "DIRTY" if (proc.stdout or "").strip() else "CLEAN"


def _resolve_summary_path(summary_arg: str, *, output_dir: Path) -> Path:
    summary_name = "main-release-verification-pack.md"
    if not summary_arg:
        candidate = output_dir / summary_name
    else:
        raw = Path(summary_arg)
        candidate = raw if raw.is_absolute() else output_dir / raw
    resolved = candidate.resolve()
    output_root = output_dir.resolve()
    if output_root == resolved or output_root in resolved.parents:
        return resolved
    raise ValueError("SUMMARY_PATH_OUTSIDE_OUTPUT_DIR")


def build_markdown_summary(payload: dict[str, object]) -> str:
    commands = payload.get("command_results", [])
    lines = [
        "# Main Release Verification Evidence Pack",
        "",
        f"- Generated at: `{payload.get('generated_at_utc', 'UNKNOWN')}`",
        f"- Git SHA: `{payload.get('git_head_sha', 'UNKNOWN')}`",
        f"- Git branch: `{payload.get('git_branch', 'UNKNOWN')}`",
        f"- Dirty tree status: `{payload.get('dirty_tree_status', 'UNKNOWN')}`",
        f"- Status: `{payload.get('status', 'UNKNOWN')}`",
        f"- Failed step: `{payload.get('failed_step', 'NONE')}`",
        "",
        "## Command Results",
        "",
        "| Name | Status | Exit | Duration (s) |",
        "|---|---|---:|---:|",
    ]
    if isinstance(commands, list):
        for result in commands:
            if not isinstance(result, dict):
                continue
            lines.append(
                f"| `{result.get('name', '?')}` | `{result.get('status', 'UNKNOWN')}` | {result.get('exit_code', '?')} | {result.get('duration_seconds', '?')} |"
            )
    blockers = payload.get("blockers", [])
    if isinstance(blockers, list) and blockers:
        lines.extend(["", "## Blockers", ""])
        for blocker in blockers:
            lines.append(f"- {blocker}")
    warnings = payload.get("warnings", [])
    if isinstance(warnings, list) and warnings:
        lines.extend(["", "## Warnings", ""])
        for warning in warnings:
            lines.append(f"- {warning}")
    lines.extend(
        [
            "",
            "## Disclaimers",
            "",
            *(f"- {disclaimer}" for disclaimer in DISCLOSURE_DISCLAIMERS),
        ]
    )
    return "\n".join(lines) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate a reproducible main release verification evidence pack.")
    parser.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--no-frontend", action="store_true")
    parser.add_argument("--no-pytest-full", action="store_true")
    parser.add_argument("--summary-markdown-output-path", default="")
    parser.add_argument("--require-pass", action="store_true")
    args = parser.parse_args(argv)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    try:
        markdown_path = _resolve_summary_path(args.summary_markdown_output_path, output_dir=output_dir)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    python_exe = sys.executable
    command_results: list[GateResult] = []
    required_failed = 0
    failed_step = ""

    for name, command in _backend_commands(python_exe, include_full_pytest=not args.no_pytest_full):
        result = _run_gate(name, command, cwd=REPO_ROOT)
        command_results.append(result)
        if result.exit_code != 0:
            required_failed += 1
            if not failed_step:
                failed_step = result.name

    if not args.no_frontend:
        for name, command, cwd in _frontend_commands():
            result = _run_gate(name, command, cwd=cwd)
            command_results.append(result)
            if result.exit_code != 0:
                required_failed += 1
                if not failed_step:
                    failed_step = result.name

    status = "PASS" if required_failed == 0 else "FAIL"
    warnings: list[str] = []
    blockers: list[str] = []
    if status == "FAIL":
        blockers.append("REQUIRED_STEP_FAILURE")
    if _dirty_tree_status() == "DIRTY":
        warnings.append("WORKTREE_DIRTY_DURING_VERIFICATION")
    payload = {
        "schema_version": "main_release_verification_pack/v1",
        "generated_at_utc": _utc_now(),
        "repo_root": str(REPO_ROOT),
        "git_head_sha": _git_head_sha(),
        "git_branch": _git_branch(),
        "dirty_tree_status": _dirty_tree_status(),
        "status": status,
        "failed_step": failed_step or None,
        "required_failed_count": required_failed,
        "warnings": warnings,
        "blockers": blockers,
        "disclaimers": list(DISCLOSURE_DISCLAIMERS),
        "output_dir": str(output_dir),
        "command_results": [asdict(result) for result in command_results],
        "environment_snapshot_redacted": redacted_environment_snapshot(dict(os.environ)),
    }

    json_path = output_dir / "main-release-verification-pack.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.write_text(build_markdown_summary(payload), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"main_release_verification_pack: {status} steps={len(command_results)} failed={required_failed}")
        print(f"json: {json_path}")
        print(f"markdown: {markdown_path}")

    if args.require_pass and required_failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
