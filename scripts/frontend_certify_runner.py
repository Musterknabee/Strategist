#!/usr/bin/env python3
"""Run Strategist web certification steps and write frontend_certify_report.json (used by certify.mjs)."""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from scripts.local_certify import (  # noqa: E402
    FRONTEND_CERTIFY_REPORT_PATH,
    FRONTEND_CERTIFY_REQUIRED_STEPS,
    FRONTEND_ROOT,
    _file_sha256,
    _frontend_source_tree_digest,
    _npm_public_registry_env,
)


def _npm_cmd() -> str:
    return shutil.which("npm") or shutil.which("npm.cmd") or "npm"


def _node_version() -> str:
    proc = subprocess.run(["node", "-v"], capture_output=True, text=True, cwd=FRONTEND_ROOT)
    return proc.stdout.strip() or "unknown"


def main() -> int:
    if not FRONTEND_ROOT.exists():
        print("frontend_certify_runner: missing frontend root", file=sys.stderr)
        return 2

    npm = _npm_cmd()
    env = os.environ.copy()
    env.update(_npm_public_registry_env())

    steps_out: list[dict[str, object]] = []
    started = datetime.now(timezone.utc)
    failed: str | None = None

    commands = {
        "contract_check": [npm, "run", "contract:check"],
        "lint": [npm, "run", "lint"],
        "typecheck": [npm, "run", "typecheck"],
        "test": [npm, "run", "test"],
        "acceptance": [npm, "run", "acceptance"],
        "build": [npm, "run", "build"],
        "audit": [npm, "run", "audit"],
    }

    for name in FRONTEND_CERTIFY_REQUIRED_STEPS:
        command = commands[name]
        t0 = time.perf_counter()
        st = datetime.now(timezone.utc).isoformat()
        # On Windows, npm lifecycle scripts resolve eslint/tsc/vitest via npm.cmd + .bin;
        # a bare argv list without shell often yields "'eslint' is not recognized".
        use_shell = os.name == "nt"
        proc = subprocess.run(
            command,
            cwd=FRONTEND_ROOT,
            env=env,
            capture_output=True,
            text=True,
            shell=use_shell,
        )
        ed = datetime.now(timezone.utc).isoformat()
        dur = round(time.perf_counter() - t0, 3)
        tail = (proc.stdout or "")[-4000:]
        terr = (proc.stderr or "")[-4000:]
        steps_out.append(
            {
                "name": name,
                "command": command,
                "cwd": str(FRONTEND_ROOT),
                "timeout_seconds": 300,
                "started_at": st,
                "finished_at": ed,
                "duration_seconds": dur,
                "exit_code": int(proc.returncode),
                "timed_out": False,
                "stdout_tail": tail,
                "stderr_tail": terr,
                "artifact_paths": [],
            }
        )
        if proc.returncode != 0 and failed is None:
            failed = name

    finished = datetime.now(timezone.utc)
    report_path = FRONTEND_CERTIFY_REPORT_PATH
    report_path.parent.mkdir(parents=True, exist_ok=True)

    payload: dict[str, object] = {
        "schema_version": "frontend_certify/v1",
        "status": "PASS" if failed is None else "FAIL",
        "failed_step": failed,
        "started_at": started.isoformat(),
        "finished_at": finished.isoformat(),
        "report_path": str(report_path),
        "node_version": _node_version(),
        "frontend_source_tree_digest": _frontend_source_tree_digest(),
        "package_json_sha256": _file_sha256(FRONTEND_ROOT / "package.json"),
        "package_lock_sha256": _file_sha256(FRONTEND_ROOT / "package-lock.json"),
        "default_step_timeout_seconds": 300,
        "steps": steps_out,
    }
    report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return 0 if failed is None else 1


if __name__ == "__main__":
    raise SystemExit(main())
