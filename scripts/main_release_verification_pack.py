#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = REPO_ROOT / "artifacts" / "release_verification" / "latest"
SENSITIVE_ENV_KEYS = ("TOKEN", "KEY", "SECRET", "PASSWORD")
SAFE_ENV_KEYS = ("STRATEGY_VALIDATOR_MODE", "STRATEGY_VALIDATOR_HOST_PORT", "PYTHONPATH")


@dataclass(frozen=True)
class GateResult:
    name: str
    command: list[str]
    exit_code: int
    duration_ms: int
    status: str
    stdout_tail: str
    stderr_tail: str


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _tail(value: str, limit: int = 4000) -> str:
    return value[-limit:] if len(value) > limit else value


def redacted_environment_snapshot(env: dict[str, str]) -> dict[str, str]:
    redacted: dict[str, str] = {}
    for key in sorted(env):
        value = env[key]
        if any(marker in key.upper() for marker in SENSITIVE_ENV_KEYS):
            redacted[key] = "<redacted>"
        elif key in SAFE_ENV_KEYS:
            redacted[key] = value
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
        command=command,
        exit_code=code,
        duration_ms=elapsed_ms,
        status="PASS" if code == 0 else "FAIL",
        stdout_tail=_tail(proc.stdout or ""),
        stderr_tail=_tail(proc.stderr or ""),
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


def build_markdown_summary(payload: dict[str, object]) -> str:
    gates = payload.get("gates", [])
    lines = [
        "# Main Release Verification Evidence Pack",
        "",
        f"- Generated at: `{payload.get('generated_at_utc', 'UNKNOWN')}`",
        f"- Status: `{payload.get('status', 'UNKNOWN')}`",
        f"- Required failed: `{payload.get('required_failed_count', 0)}`",
        "",
        "## Gate Results",
        "",
        "| Gate | Status | Exit | Duration (ms) |",
        "|---|---|---:|---:|",
    ]
    if isinstance(gates, list):
        for gate in gates:
            if not isinstance(gate, dict):
                continue
            lines.append(
                f"| `{gate.get('name', '?')}` | `{gate.get('status', 'UNKNOWN')}` | {gate.get('exit_code', '?')} | {gate.get('duration_ms', '?')} |"
            )
    lines.extend(
        [
            "",
            "## Disclaimers",
            "",
            "- Local verification only.",
            "- Not production deployment approval.",
            "- Not operator signoff.",
            "- Not live trading authorization.",
            "- Not profitability evidence.",
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

    python_exe = sys.executable
    gate_results: list[GateResult] = []
    required_failed = 0

    for name, command in _backend_commands(python_exe, include_full_pytest=not args.no_pytest_full):
        result = _run_gate(name, command, cwd=REPO_ROOT)
        gate_results.append(result)
        if result.exit_code != 0:
            required_failed += 1

    if not args.no_frontend:
        for name, command, cwd in _frontend_commands():
            result = _run_gate(name, command, cwd=cwd)
            gate_results.append(result)
            if result.exit_code != 0:
                required_failed += 1

    status = "PASS" if required_failed == 0 else "FAIL"
    payload = {
        "schema_version": "main_release_verification_pack/v1",
        "generated_at_utc": _utc_now(),
        "status": status,
        "required_failed_count": required_failed,
        "repo_root": str(REPO_ROOT),
        "output_dir": str(output_dir),
        "gates": [asdict(result) for result in gate_results],
        "environment_snapshot_redacted": redacted_environment_snapshot(dict(os.environ)),
    }

    json_path = output_dir / "main-release-verification-pack.json"
    json_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    if args.summary_markdown_output_path:
        markdown_path = Path(args.summary_markdown_output_path).resolve()
        markdown_path.parent.mkdir(parents=True, exist_ok=True)
        markdown_path.write_text(build_markdown_summary(payload), encoding="utf-8")
    else:
        markdown_path = output_dir / "main-release-verification-pack.md"
        markdown_path.write_text(build_markdown_summary(payload), encoding="utf-8")

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"main_release_verification_pack: {status} gates={len(gate_results)} failed={required_failed}")
        print(f"json: {json_path}")
        print(f"markdown: {markdown_path}")

    if args.require_pass and required_failed > 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
