#!/usr/bin/env python3
"""Run the same local gates as CI validate (no network beyond optional snapshot generation).

Exit code is the first failing step. Use --json for a machine-readable summary.
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


def _run_step(name: str, command: list[str], *, cwd: Path) -> StepResult:
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
    if proc.stdout:
        sys.stdout.buffer.write(proc.stdout.encode("utf-8", "replace"))
    if proc.stderr:
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
    args = parser.parse_args(argv)

    root = _repo_root()
    py = [sys.executable]

    steps: list[tuple[str, list[str]]] = [
        ("compileall", py + ["-m", "compileall", "-q", "strategy_validator", "scripts", "tests"]),
        ("source_health", py + [str(root / "scripts" / "source_health.py"), "--json"]),
        ("repository_truth_check", py + [str(root / "scripts" / "repository_truth_check.py"), "--json"]),
        ("migration_truth_check", py + [str(root / "scripts" / "migration_truth_check.py")]),
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
        ("pytest", py + ["-m", "pytest", "-q"]),
    ]

    results: list[StepResult] = []
    failed: StepResult | None = None
    for name, cmd in steps:
        res = _run_step(name, cmd, cwd=root)
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
    print("\nci_local_verify: PASS", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
