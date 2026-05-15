#!/usr/bin/env python3
"""Remove or plan removal of transient frontend directories (local_certify proof)."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_ROOT = REPO_ROOT / "ui" / "strategist-web"


def _rmtree_force(path: Path) -> None:
    def _onerror(func, target: str, exc_info) -> None:  # type: ignore[no-untyped-def]
        if not os.path.isdir(target):
            raise exc_info[1]
        os.chmod(target, stat.S_IWRITE)
        func(target)

    shutil.rmtree(path, onerror=_onerror)


def _release_windows_frontend_locks() -> None:
    """Best-effort: stop Next dev listeners that hold SWC/node_modules open."""
    if os.name != "nt":
        return
    ps = (
        "Get-NetTCPConnection -LocalPort 3000,3001 -State Listen -ErrorAction SilentlyContinue | "
        "ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"
    )
    subprocess.run(
        ["powershell", "-NoProfile", "-Command", ps],
        check=False,
        capture_output=True,
        text=True,
    )
    time.sleep(1.0)


def _remove_tree_with_retries(path: Path, *, attempts: int = 6, pause_seconds: float = 2.0) -> str | None:
    """Remove a directory tree; retry for transient Windows/OneDrive file locks."""
    last_error: str | None = None
    for attempt in range(attempts):
        if not path.exists():
            return None
        try:
            _rmtree_force(path)
            if not path.exists():
                return None
            last_error = "remove_failed:path_still_exists"
        except OSError as exc:
            last_error = f"remove_failed:{exc}"
        if attempt + 1 < attempts:
            time.sleep(pause_seconds)
    return last_error


def clean_frontend_workspace(*, output: Path, dry_run: bool = False) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    if not dry_run:
        _release_windows_frontend_locks()
    paths_payload: list[dict[str, object]] = []
    blockers: list[str] = []
    targets = (
        ("node_modules", FRONTEND_ROOT / "node_modules"),
        (".next", FRONTEND_ROOT / ".next"),
        ("coverage", FRONTEND_ROOT / "coverage"),
    )
    for name, path in targets:
        existed = path.exists()
        removed = False
        skipped_reason: str | None = None
        if existed and not dry_run:
            skipped_reason = _remove_tree_with_retries(path)
            removed = skipped_reason is None and not path.exists()
            if skipped_reason is not None:
                blockers.append(f"{name}:{skipped_reason}")
        elif dry_run:
            skipped_reason = "dry_run"
        paths_payload.append(
            {
                "name": name,
                "path": str(path.resolve()),
                "existed": existed,
                "removed": removed,
                "skipped_reason": skipped_reason,
            }
        )
    finished = datetime.now(timezone.utc).isoformat()
    payload: dict[str, object] = {
        "schema_version": "frontend_clean_workspace/v1",
        "status": "PASS" if not blockers else "FAIL",
        "repo_root": str(REPO_ROOT),
        "frontend_root": str(FRONTEND_ROOT.resolve()),
        "dry_run": dry_run,
        "started_at": started,
        "finished_at": finished,
        "paths": paths_payload,
        "blockers": blockers,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print a short machine-readable summary to stdout (local_certify parity).",
    )
    ns = parser.parse_args(argv)
    payload = clean_frontend_workspace(output=ns.output, dry_run=bool(ns.dry_run))
    if ns.json:
        print(
            json.dumps(
                {
                    "schema_version": payload.get("schema_version"),
                    "status": payload.get("status"),
                    "output": str(ns.output.resolve()),
                },
                sort_keys=True,
            )
        )
    if payload.get("status") != "PASS":
        blockers = payload.get("blockers") or []
        print("frontend_clean_workspace: FAIL", file=sys.stderr)
        for item in blockers:
            print(f"  blocker: {item}", file=sys.stderr)
        print(
            "hint: stop npm run dev, pause OneDrive on this repo, then re-run clean_frontend_workspace.py",
            file=sys.stderr,
        )
    return 0 if payload.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
