from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.migration_truth_check import run_migration_truth_check

REPO_ROOT = Path(__file__).resolve().parents[2]


def _symlink_to_repo(tmp_path: Path) -> Path:
    link = tmp_path / "repo-link"
    link.symlink_to(REPO_ROOT, target_is_directory=True)
    return link


def test_migration_truth_check_rejects_symlinked_repo_root(tmp_path: Path) -> None:
    report = run_migration_truth_check(repo_root=_symlink_to_repo(tmp_path))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["first_schema_version"] == 0
    assert payload["second_schema_version"] == 0
    assert len(payload["failures"]) == 1
    assert payload["failures"][0]["name"] == "repo_root_path_integrity"
    assert "MIGRATION_TRUTH_REPO_ROOT_IS_SYMLINK" in payload["failures"][0]["detail"]


def test_migration_truth_check_rejects_repo_root_under_symlinked_parent(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    link_parent = tmp_path / "link-parent"
    link_parent.symlink_to(real_parent, target_is_directory=True)
    nested = link_parent / "repo"
    nested.mkdir()

    report = run_migration_truth_check(repo_root=nested)

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert "MIGRATION_TRUTH_REPO_ROOT_PARENT_IS_SYMLINK" in payload["failures"][0]["detail"]


def test_migration_truth_check_cli_reports_structured_symlinked_repo_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/migration_truth_check.py",
            "--repo-root",
            str(_symlink_to_repo(tmp_path)),
            "--json",
        ],
        cwd=REPO_ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["status"] == "FAIL"
    assert payload["failures"][0]["name"] == "repo_root_path_integrity"
    assert "MIGRATION_TRUTH_REPO_ROOT_IS_SYMLINK" in payload["failures"][0]["detail"]
