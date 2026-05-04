#!/usr/bin/env python3
"""Remove bounded local transient trees (bytecode caches) under trusted repo subtrees.

Default is **dry-run** (no deletions). Use ``--apply`` to delete. Intended for developer
worktrees before handoff ZIPs or after long pytest runs — it does **not** replace
``strategy_validator.cli.hygiene_check`` (which enforces fail-closed repo policy).
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from scripts._path_integrity import PathIntegrityError, safe_input_dir, symlink_components_preserving_path

# Only descend these top-level directories (never .git, node_modules roots, scratch wholesale).
_SAFE_TOP_LEVEL = frozenset({"strategy_validator", "tests", "scripts", "docs", "configs"})


@dataclass(frozen=True)
class PurgePlanEntry:
    kind: str
    path: str


@dataclass(frozen=True)
class PurgeReport:
    schema_version: str
    status: str
    repo_root: str
    dry_run: bool
    planned_deletions: tuple[PurgePlanEntry, ...]
    deleted_count: int
    skipped_symlink: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "status": self.status,
            "repo_root": self.repo_root,
            "dry_run": self.dry_run,
            "planned_deletions": [asdict(x) for x in self.planned_deletions],
            "planned_count": len(self.planned_deletions),
            "deleted_count": self.deleted_count,
            "skipped_symlink": list(self.skipped_symlink),
        }


def _plan_transient_dirs(repo_root: Path) -> tuple[PurgePlanEntry, ...]:
    planned: list[PurgePlanEntry] = []
    for top in sorted(_SAFE_TOP_LEVEL):
        base = repo_root / top
        if not base.is_dir():
            continue
        for current, dirnames, filenames in os.walk(base, topdown=True):
            cur_path = Path(current)
            rel = cur_path.relative_to(repo_root)
            if rel.parts and rel.parts[0] not in _SAFE_TOP_LEVEL:
                dirnames[:] = []
                continue
            if cur_path.name == "__pycache__":
                planned.append(PurgePlanEntry(kind="dir", path=str(cur_path.resolve())))
                dirnames[:] = []
                continue
            for name in filenames:
                if name.endswith((".pyc", ".pyo")):
                    p = cur_path / name
                    planned.append(PurgePlanEntry(kind="file", path=str(p.resolve())))
    return tuple(sorted(planned, key=lambda e: e.path))


def _delete_planned(entries: tuple[PurgePlanEntry, ...]) -> tuple[int, list[str]]:
    deleted = 0
    skipped: list[str] = []
    for entry in entries:
        path = Path(entry.path)
        symlinks = symlink_components_preserving_path(path)
        if symlinks:
            skipped.append(str(path))
            continue
        try:
            if entry.kind == "dir" and path.is_dir():
                shutil.rmtree(path, ignore_errors=False)
                deleted += 1
            elif entry.kind == "file" and path.is_file():
                path.unlink()
                deleted += 1
        except OSError:
            skipped.append(str(path))
    return deleted, skipped


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, default=None, help="Repository root (default: parent of this script)")
    p.add_argument(
        "--apply",
        action="store_true",
        help="Perform deletions (default is dry-run: plan only, no filesystem changes)",
    )
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    try:
        root = safe_input_dir(ns.repo_root or _REPO_ROOT, label="PURGE_REPO_ROOT", required=True)
    except PathIntegrityError as exc:
        payload = {"schema_version": "purge_repo_transients_path_error/v1", "ok": False, "error": str(exc)}
        sys.stdout.write(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True) + "\n")
        return 2
    assert root is not None
    root = root.resolve()

    planned = _plan_transient_dirs(root)
    dry_run = not ns.apply
    deleted = 0
    skipped_symlink: tuple[str, ...] = ()
    if not dry_run:
        deleted, skip_list = _delete_planned(planned)
        skipped_symlink = tuple(skip_list)

    report = PurgeReport(
        schema_version="purge_repo_transients/v1",
        status="PASS",
        repo_root=str(root),
        dry_run=dry_run,
        planned_deletions=planned,
        deleted_count=deleted,
        skipped_symlink=skipped_symlink,
    )
    out = report.to_payload()
    if ns.json:
        sys.stdout.write(json.dumps(out, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(
            f"purge_repo_transients: dry_run={dry_run} planned={len(planned)} deleted={deleted} repo={root}\n"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
