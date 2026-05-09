from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.cli.release_candidate_bundle import cmd_verify_bundle
from strategy_validator.cli.release_candidate_common import (
    REPO_ROOT,
    CmdResult,
    _candidate_dir,
    _ensure_dir,
    _is_windows,
    _run,
    _utc_now_iso,
    _which,
    _write_json,
    _write_text,
)


def _write_check_log(out_dir: Path, name: str, result: CmdResult) -> None:
    log_path = out_dir / "checks" / f"{name}.log"
    _write_text(
        log_path,
        "\n".join(
            [
                f"command: {name}",
                f"ok: {result.ok}",
                f"exit_code: {result.exit_code}",
                f"duration_ms: {result.duration_ms}",
                "",
                "----- stdout -----",
                result.stdout.rstrip(),
                "",
                "----- stderr -----",
                result.stderr.rstrip(),
                "",
            ]
        ),
    )


def cmd_assess(candidate: str, *, skip_frontend: bool, full_suite: bool = False) -> dict[str, Any]:
    out_dir = _candidate_dir(candidate)
    if not out_dir.exists():
        raise SystemExit(f"candidate directory does not exist: {out_dir}")
    _ensure_dir(out_dir / "checks")

    checks: list[dict[str, Any]] = []

    started = datetime.now(timezone.utc)
    try:
        bundle_payload = cmd_verify_bundle(candidate)
        bundle_duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        checks.append(
            {
                "name": "bundle-verify",
                "ok": bool(bundle_payload.get("ok")),
                "exit_code": 0 if bundle_payload.get("ok") else 1,
                "duration_ms": bundle_duration_ms,
            }
        )
    except SystemExit:
        bundle_duration_ms = int((datetime.now(timezone.utc) - started).total_seconds() * 1000)
        checks.append({"name": "bundle-verify", "ok": False, "exit_code": 1, "duration_ms": bundle_duration_ms})
        _write_json(
            out_dir / "assessment.json",
            {
                "schema": 2,
                "candidate": candidate,
                "assessed_at": _utc_now_iso(),
                "checks": checks,
                "architecture_health_report_ok": False,
            },
        )
        raise

    def run_check(name: str, cmd: list[str], cwd: Path, env: dict[str, str] | None = None, timeout_s: int | None = None) -> None:
        res = _run(cmd, cwd=cwd, env=env, timeout_s=timeout_s)
        _write_check_log(out_dir, name, res)
        checks.append({"name": name, "ok": res.ok, "exit_code": res.exit_code, "duration_ms": res.duration_ms})
        if not res.ok:
            raise SystemExit(f"assessment failed at {name} (see {out_dir / 'checks' / f'{name}.log'})")

    run_check("source-health", [sys.executable, "scripts/source_health.py"], cwd=REPO_ROOT)
    run_check("repository-truth", [sys.executable, "scripts/repository_truth_check.py"], cwd=REPO_ROOT)
    run_check("migration-truth", [sys.executable, "scripts/migration_truth_check.py"], cwd=REPO_ROOT)
    run_check("environment-check", [sys.executable, "scripts/environment_check.py", "--include-extra", "dev"], cwd=REPO_ROOT)

    run_check(
        "hygiene",
        [sys.executable, "-c", "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"],
        cwd=REPO_ROOT,
        env={"PYTHONDONTWRITEBYTECODE": "1"},
    )
    run_check(
        "constitutional",
        [sys.executable, "-m", "pytest", "-q", "tests/constitutional/test_anti_regression_invariants.py"],
        cwd=REPO_ROOT,
    )

    if full_suite:
        run_check(
            "full-suite",
            [sys.executable, "-m", "pytest", "-q"],
            cwd=REPO_ROOT,
        )

    web_dir = REPO_ROOT / "ui" / "strategist-web"
    frontend_status: dict[str, Any] = {
        "name": "frontend-operator-ui",
        "present": web_dir.exists(),
        "skipped": bool(skip_frontend),
        "status": "DEFERRED" if not web_dir.exists() else "PRESENT",
        "detail": "ui/strategist-web is absent; backend assessment cannot imply frontend readiness." if not web_dir.exists() else "ui/strategist-web package exists.",
    }
    if skip_frontend:
        checks.append({"name": "frontend-validate", "ok": True, "exit_code": 0, "duration_ms": 0, "skipped": True, "detail": frontend_status["detail"]})
    else:
        if _which("npm") is None and _which("npm.cmd") is None:
            raise SystemExit("frontend assessment requested but npm not found on PATH")
        if not web_dir.exists():
            raise SystemExit("frontend assessment requested but ui/strategist-web is missing")
        if _is_windows():
            run_check(
                "frontend-validate",
                ["cmd", "/d", "/s", "/c", "npm run validate"],
                cwd=web_dir,
            )
        else:
            run_check("frontend-validate", ["npm", "run", "validate"], cwd=web_dir)

    health = _run([sys.executable, "scripts/architecture_health_report.py"], cwd=REPO_ROOT)
    _write_check_log(out_dir, "architecture-health", health)

    assessment = {
        "schema": 2,
        "candidate": candidate,
        "assessed_at": _utc_now_iso(),
        "checks": checks,
        "architecture_health_report_ok": health.ok,
        "frontend_status": frontend_status,
        "full_suite_requested": bool(full_suite),
    }
    _write_json(out_dir / "assessment.json", assessment)
    _write_text(
        out_dir / "assessment.md",
        "\n".join(
            [
                f"# Production candidate assessment: `{candidate}`",
                "",
                f"- Assessed: `{assessment['assessed_at']}`",
                "",
                "## Checks",
                "",
                *[f"- {c['name']}: {'PASS' if c['ok'] else 'FAIL'} ({c['duration_ms']} ms)" for c in checks],
                "",
                f"- Architecture health report: {'PASS' if health.ok else 'FAIL'}",
                f"- Frontend operator UI: {frontend_status['status']} ({'skipped' if frontend_status['skipped'] else 'checked'})",
                f"  - {frontend_status['detail']}",
                "",
            ]
        ),
    )
    if not health.ok:
        raise SystemExit(f"assessment failed at architecture-health (see {out_dir / 'checks' / 'architecture-health.log'})")

    return assessment
