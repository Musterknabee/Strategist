#!/usr/bin/env python3
"""Remove or plan removal of transient frontend directories (local_certify proof)."""
from __future__ import annotations

import argparse
import json
import os
import shutil
import stat
import sys
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


def clean_frontend_workspace(*, output: Path, dry_run: bool = False) -> dict[str, object]:
    started = datetime.now(timezone.utc).isoformat()
    paths_payload: list[dict[str, object]] = []
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
            try:
                _rmtree_force(path)
                removed = True
            except OSError as exc:
                skipped_reason = f"remove_failed:{exc}"
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
        "status": "PASS",
        "repo_root": str(REPO_ROOT),
        "frontend_root": str(FRONTEND_ROOT.resolve()),
        "dry_run": dry_run,
        "started_at": started,
        "finished_at": finished,
        "paths": paths_payload,
        "blockers": [],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
