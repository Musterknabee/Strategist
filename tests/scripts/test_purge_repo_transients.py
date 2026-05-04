"""Tests for scripts/purge_repo_transients.py."""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

from scripts.purge_repo_transients import main


def test_purge_dry_run_lists_bytecode_under_safe_roots(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    cache = root / "strategy_validator" / "pkg" / "__pycache__"
    cache.mkdir(parents=True)
    pyc = cache / "x.cpython-312.pyc"
    pyc.write_bytes(b"\x00")
    loose_dir = root / "tests"
    loose_dir.mkdir(parents=True, exist_ok=True)
    loose = loose_dir / "orphan.pyc"
    loose.write_bytes(b"\x00")

    buf = io.StringIO()
    old = sys.stdout
    try:
        sys.stdout = buf
        assert main(["--repo-root", str(root), "--json"]) == 0
    finally:
        sys.stdout = old
    payload = json.loads(buf.getvalue())
    assert payload["dry_run"] is True
    paths = {e["path"] for e in payload["planned_deletions"]}
    assert str(cache.resolve()) in paths
    assert str(loose.resolve()) in paths


def test_purge_apply_removes_planned_paths(tmp_path: Path) -> None:
    root = tmp_path.resolve()
    cache = root / "scripts" / "__pycache__"
    cache.mkdir(parents=True)
    pyc = cache / "m.pyc"
    pyc.write_bytes(b"\x00")

    assert main(["--repo-root", str(root), "--apply"]) == 0
    assert not cache.exists()
