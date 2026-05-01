#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.frontend_readiness_claim import (  # noqa: E402
    FRONTEND_EXPECTED_PACKAGE,
    FRONTEND_READINESS_CLAIM_SCHEMA_VERSION,
    default_frontend_readiness_claim_path,
)


def _run(command: list[str], *, cwd: Path) -> dict[str, object]:
    if command and command[0] == "npm":
        command = [shutil.which("npm") or shutil.which("npm.cmd") or "npm.cmd", *command[1:]]
    if command and command[0] == "rg":
        command = [shutil.which("rg") or "rg", *command[1:]]
    started = time.perf_counter()
    completed = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    return {
        "command": command,
        "cwd": str(cwd),
        "returncode": completed.returncode,
        "duration_ms": int((time.perf_counter() - started) * 1000),
        "stdout_tail": completed.stdout[-4000:],
        "stderr_tail": completed.stderr[-4000:],
        "ok": completed.returncode == 0,
    }


def _http_json(url: str) -> tuple[bool, int | None, dict[str, object] | None, str | None]:
    req = Request(url, headers={"Accept": "application/json,*/*;q=0.8"}, method="GET")
    try:
        with urlopen(req, timeout=15) as resp:  # noqa: S310
            body = resp.read()
            status = int(getattr(resp, "status", 200))
    except URLError as exc:
        return False, None, None, str(exc)[:300]
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError):
        parsed = None
    return status == 200, status, parsed if isinstance(parsed, dict) else None, None


def _http_text(url: str) -> tuple[bool, int | None, str | None]:
    req = Request(url, headers={"Accept": "text/html,*/*;q=0.8"}, method="GET")
    try:
        with urlopen(req, timeout=15) as resp:  # noqa: S310
            body = resp.read(300_000)
            status = int(getattr(resp, "status", 200))
    except URLError as exc:
        return False, None, str(exc)[:300]
    text = body.decode("utf-8", errors="replace")
    return status == 200 and "STRATEGIST TERMINAL" in text, status, None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Claim single-tenant frontend readiness after formal local evidence gates pass.")
    parser.add_argument("--api-base-url", default="http://127.0.0.1:8010")
    parser.add_argument("--frontend-url", default="http://127.0.0.1:3000")
    parser.add_argument("--output", type=Path, default=default_frontend_readiness_claim_path(REPO_ROOT))
    parser.add_argument("--skip-build", action="store_true", help="Use only lint/typecheck/test plus live smoke checks.")
    args = parser.parse_args(argv)

    web = REPO_ROOT / FRONTEND_EXPECTED_PACKAGE
    frontend_prebuild_ok, frontend_prebuild_status, frontend_prebuild_error = _http_text(args.frontend_url.rstrip("/") + "/")

    command_results = [
        _run(["npm", "run", "lint"], cwd=web),
        _run(["npm", "run", "typecheck"], cwd=web),
        _run(["npm", "run", "test"], cwd=web),
    ]
    if not args.skip_build:
        command_results.append(_run(["npm", "run", "build"], cwd=web))

    token_scan = _run(["rg", "STRATEGY_VALIDATOR_API_TOKEN|NEXT_PUBLIC_.*TOKEN", str(web), "-n"], cwd=REPO_ROOT)
    no_public_token_exposure = token_scan["returncode"] == 1

    ready_ok, ready_status, ready_payload, ready_error = _http_json(args.api_base_url.rstrip("/") + "/readyz")
    facade_ok, facade_status, facade_payload, facade_error = _http_json(args.api_base_url.rstrip("/") + "/ui/facade")
    frontend_postbuild_ok, frontend_postbuild_status, frontend_postbuild_error = _http_text(args.frontend_url.rstrip("/") + "/")
    frontend_ok = frontend_prebuild_ok or frontend_postbuild_ok

    checks = {
        "frontend_package_present": (web / "package.json").is_file(),
        "lint_passed": command_results[0]["ok"] is True,
        "typecheck_passed": command_results[1]["ok"] is True,
        "test_passed": command_results[2]["ok"] is True,
        "build_passed": True if args.skip_build else command_results[3]["ok"] is True,
        "no_public_token_exposure": no_public_token_exposure,
        "api_ready": ready_ok and (ready_payload or {}).get("status") == "READY",
        "facade_read_plane_only": facade_ok and (facade_payload or {}).get("read_plane_only") is True,
        "frontend_runtime_reachable": frontend_ok,
    }
    ok = all(checks.values())
    payload = {
        "schema_version": FRONTEND_READINESS_CLAIM_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "deployment_model": "single_tenant",
        "frontend_expected_package": FRONTEND_EXPECTED_PACKAGE,
        "frontend_readiness_claimed": ok,
        "frontend_runtime_reachable": frontend_ok,
        "ok": ok,
        "claim_scope": "local_single_tenant_operator_console",
        "api_base_url": args.api_base_url,
        "frontend_url": args.frontend_url,
        "checks": checks,
        "command_results": command_results,
        "http_checks": {
            "readyz": {"ok": ready_ok, "status": ready_status, "error": ready_error},
            "facade": {"ok": facade_ok, "status": facade_status, "error": facade_error},
            "frontend_prebuild": {"ok": frontend_prebuild_ok, "status": frontend_prebuild_status, "error": frontend_prebuild_error},
            "frontend_postbuild": {"ok": frontend_postbuild_ok, "status": frontend_postbuild_status, "error": frontend_postbuild_error},
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "ok": ok,
                "output": str(args.output),
                "checks": checks,
                "runtime_note": (
                    "The API ignores this artifact for /ui/facade unless "
                    "STRATEGY_VALIDATOR_FRONTEND_READINESS_CLAIM_ENABLE is set to true/1/on for that process "
                    "(backend-only default; not production certification)."
                ),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
