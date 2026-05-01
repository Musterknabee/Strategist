#!/usr/bin/env python3
"""Run strategist-web lint, typecheck, tests, build; optionally API smoke when base URL is set."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _run(cmd: list[str], *, cwd: Path, env: dict[str, str]) -> tuple[int, str]:
    proc = subprocess.run(cmd, cwd=cwd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
    out = (proc.stdout or "") + (proc.stderr or "")
    return int(proc.returncode), out[-8000:]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke-api-base",
        default=os.environ.get("STRATEGIST_SMOKE_API_BASE_URL", ""),
        help="If set, run ui/strategist-web smoke against this API base (e.g. http://127.0.0.1:8000).",
    )
    parser.add_argument("--skip-install", action="store_true", help="Do not run npm ci (use existing node_modules).")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary to stdout.")
    args = parser.parse_args(argv)

    root = _repo_root()
    web = root / "ui" / "strategist-web"
    if not web.is_dir() or not (web / "package.json").is_file():
        print("verify_frontend: missing ui/strategist-web/package.json", file=sys.stderr)
        return 2

    npm = shutil.which("npm")
    if not npm:
        print("verify_frontend: npm not found on PATH", file=sys.stderr)
        return 2

    env = os.environ.copy()
    node_path = str(web / "node_modules" / ".bin")
    if node_path not in env.get("PATH", ""):
        env["PATH"] = node_path + os.pathsep + env.get("PATH", "")

    steps: list[tuple[str, list[str]]] = []
    if not args.skip_install:
        steps.append(("npm_ci", [npm, "ci"]))

    steps.extend(
        [
            ("npm_lint", [npm, "run", "lint"]),
            ("npm_typecheck", [npm, "run", "typecheck"]),
            ("npm_test", [npm, "run", "test"]),
            ("npm_build", [npm, "run", "build"]),
        ]
    )

    results: list[dict[str, object]] = []
    failed: str | None = None

    for name, cmd in steps:
        code, tail = _run(cmd, cwd=web, env=env)
        results.append({"name": name, "exit_code": code, "output_tail": tail})
        if code != 0 and failed is None:
            failed = name
            break

    smoke_ok: bool | None = None
    smoke_detail = ""
    if not failed and args.smoke_api_base.strip():
        env_smoke = env.copy()
        env_smoke["STRATEGIST_SMOKE_API_BASE_URL"] = args.smoke_api_base.strip()
        code, tail = _run([npm, "run", "smoke", "--", "--json"], cwd=web, env=env_smoke)
        smoke_ok = code == 0
        smoke_detail = tail
        results.append({"name": "npm_smoke", "exit_code": code, "output_tail": tail})
        if code != 0:
            failed = "npm_smoke"

    summary = {
        "schema_version": "verify_frontend/v1",
        "status": "PASS" if failed is None else "FAIL",
        "failed_step": failed,
        "smoke_ran": bool(args.smoke_api_base.strip()),
        "smoke_ok": smoke_ok,
        "steps": results,
    }
    if args.json:
        print(json.dumps(summary, indent=2))
    else:
        print(f"verify_frontend: {summary['status']}")
        if failed:
            print(f"Failed at: {failed}", file=sys.stderr)
            for row in results:
                if row.get("name") == failed:
                    print(row.get("output_tail", ""), file=sys.stderr)

    return 0 if failed is None else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
