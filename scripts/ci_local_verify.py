#!/usr/bin/env python3
"""Run the same local gates as CI validate (no network beyond optional snapshot generation).

Exit code is the first failing step. Use --json for a machine-readable summary.

Windows note: do not infer pytest pass/fail by piping ``python -m pytest`` into ``findstr``
(or similar). ``findstr`` exits 1 when no lines match, so an all-green pytest run can
produce a false failure. This script runs pytest via subprocess and uses its return code
only; see docs/development/WINDOWS_PYTEST_VERIFICATION.md.
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class StepResult:
    name: str
    command: list[str]
    exit_code: int
    stderr_tail: str


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run_step(name: str, command: list[str], *, cwd: Path, quiet_transcript: bool = False) -> StepResult:
    if not quiet_transcript:
        print(f"\n=== {name} ===", flush=True)
        print("+ " + " ".join(command), flush=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd)
    if name == "pytest":
        for key in (
            "STRATEGY_VALIDATOR_MODE",
            "STRATEGY_VALIDATOR_API_TOKEN",
            "STRATEGY_VALIDATOR_API_TOKEN_SCOPES",
            "STRATEGY_VALIDATOR_LEDGER_DB_PATH",
            "STRATEGY_VALIDATOR_ARTIFACT_ROOT",
            "STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR",
        ):
            env.pop(key, None)
    proc = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.stdout and not quiet_transcript:
        sys.stdout.buffer.write(proc.stdout.encode("utf-8", "replace"))
    if proc.stderr and (not quiet_transcript or proc.returncode != 0):
        sys.stderr.buffer.write(proc.stderr.encode("utf-8", "replace"))
    tail = (proc.stderr or "")[-4000:]
    return StepResult(name=name, command=command, exit_code=int(proc.returncode), stderr_tail=tail)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-fail-fast",
        action="store_true",
        help="Run all steps even after a failure (exit code is still non-zero if any step failed).",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout (final line only).")
    parser.add_argument(
        "--json-summary-only",
        action="store_true",
        help="With --json, suppress per-step transcripts on stdout/stderr so the only stdout is valid JSON (for evidence capture).",
    )
    parser.add_argument(
        "--include-frontend",
        action="store_true",
        help="After backend gates, run scripts/verify_frontend.py (lint/typecheck/test/build; no API smoke unless STRATEGIST_SMOKE_API_BASE_URL is set).",
    )
    args = parser.parse_args(argv)

    root = _repo_root()
    py = [sys.executable]

    steps: list[tuple[str, list[str]]] = [
        ("compileall", py + ["-m", "compileall", "-q", "strategy_validator", "scripts", "tests"]),
        ("source_health", py + [str(root / "scripts" / "source_health.py"), "--json"]),
        ("repository_truth_check", py + [str(root / "scripts" / "repository_truth_check.py"), "--json"]),
        ("migration_truth_check", py + [str(root / "scripts" / "migration_truth_check.py")]),
        ("purge_repo_transients_dry_run", py + [str(root / "scripts" / "purge_repo_transients.py"), "--json"]),
        (
            "import_linter",
            py
            + [
                "-c",
                "from click.testing import CliRunner; "
                "from importlinter.cli import lint_imports_command; "
                "r=CliRunner().invoke(lint_imports_command, []); "
                "import sys; "
                "sys.stdout.buffer.write((r.output or '').encode('utf-8','replace')); "
                "raise SystemExit(r.exit_code)",
            ],
        ),
        ("openapi_contract_snapshot", py + [str(root / "scripts" / "openapi_contract_snapshot.py"), "--check"]),
        (
            "ui_facade_contract_snapshot",
            py + [str(root / "scripts" / "ui_facade_contract_snapshot.py"), "--check", "--no-static-fallback"],
        ),
        (
            "thesis_mutation_batch_loop_cli_help",
            py + ["-m", "strategy_validator.cli.thesis_mutation_batch_loop", "--help"],
        ),
        (
            "research_os_runtime_demo_cli_help",
            py + ["-m", "strategy_validator.cli.research_os_runtime_demo", "--help"],
        ),
        ("pytest", py + ["-m", "pytest", "-q"]),
    ]
    if args.include_frontend:
        steps.append(("frontend_verify", py + [str(root / "scripts" / "verify_frontend.py"), "--json"]))

    results: list[StepResult] = []
    failed: StepResult | None = None
    for name, cmd in steps:
        res = _run_step(name, cmd, cwd=root, quiet_transcript=bool(args.json and args.json_summary_only))
        results.append(res)
        if res.exit_code != 0 and failed is None:
            failed = res
            if not args.no_fail_fast:
                break

    summary = {
        "schema_version": "ci_local_verify/v1",
        "status": "PASS" if failed is None else "FAIL",
        "failed_step": None if failed is None else failed.name,
        "steps": [asdict(r) for r in results],
    }
    if args.json:
        print(json.dumps(summary, indent=2))

    if failed is not None:
        print(f"\nci_local_verify: FAIL at step {failed.name!r} (exit {failed.exit_code})", file=sys.stderr, flush=True)
        return failed.exit_code or 1
    # With --json, stdout must be only the JSON document (for evidence capture).
    if args.json:
        print("ci_local_verify: PASS", file=sys.stderr, flush=True)
    else:
        print("\nci_local_verify: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
