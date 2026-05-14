from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any

from strategy_validator.cli.release_candidate_common import (
    ARTIFACTS_ROOT,
    REPO_ROOT,
    _ensure_dir,
    _utc_now_iso,
    _write_json,
)

def cmd_cleanup(*, aggressive_frontend: bool) -> dict[str, Any]:
    removed: list[str] = []

    def rm_tree(rel: Path) -> None:
        abs_path = REPO_ROOT / rel
        if abs_path.exists() and abs_path.is_dir():
            shutil.rmtree(abs_path, ignore_errors=True)
            removed.append(rel.as_posix() + "/")

    def rm_glob(pattern: str) -> None:
        for p in REPO_ROOT.rglob(pattern):
            if p.is_file():
                try:
                    p.unlink()
                    removed.append(str(p.relative_to(REPO_ROOT)).replace("\\", "/"))
                except OSError:
                    continue

    def rm_named_dirs(name: str) -> None:
        for p in sorted(REPO_ROOT.rglob(name), key=lambda item: len(item.parts), reverse=True):
            if p.is_dir():
                rel = p.relative_to(REPO_ROOT).as_posix() + "/"
                shutil.rmtree(p, ignore_errors=True)
                removed.append(rel)

    rm_tree(Path(".import_linter_cache"))
    rm_tree(Path(".strategy_validator"))
    rm_tree(Path(".pytest_cache"))
    rm_tree(Path(".mypy_cache"))
    rm_tree(Path(".ruff_cache"))
    rm_named_dirs("__pycache__")
    rm_glob("*.pyc")
    rm_glob("*.pyo")

    if aggressive_frontend:
        rm_tree(Path("ui/strategist-web/.next"))
        rm_tree(Path("ui/strategist-web/node_modules"))

    payload = {"schema": 1, "cleaned_at": _utc_now_iso(), "removed": sorted(set(removed))}
    _ensure_dir(ARTIFACTS_ROOT)
    _write_json(ARTIFACTS_ROOT / "cleanup.json", payload)
    return payload
