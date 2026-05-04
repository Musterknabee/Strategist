from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.source_health import run_source_health

REPO_ROOT = Path(__file__).resolve().parents[2]


def _minimal_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "ok.py").write_text("x = 1\n", encoding="utf-8")
    return repo


def test_source_health_rejects_symlinked_scan_root_file(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    link = repo / "linked.py"
    link.symlink_to(repo / "ok.py")

    report = run_source_health(repo_root=repo, roots=("linked.py",))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checked_file_count"] == 0
    assert payload["failure_count"] == 1
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_SCAN_ROOT_IS_SYMLINK"


def test_source_health_rejects_scan_root_under_symlinked_parent(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_dir = tmp_path / "real-src"
    real_dir.mkdir()
    (real_dir / "nested.py").write_text("y = 2\n", encoding="utf-8")
    (repo / "linked_dir").symlink_to(real_dir, target_is_directory=True)

    report = run_source_health(repo_root=repo, roots=("linked_dir/nested.py",))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checked_file_count"] == 0
    assert payload["failure_count"] == 1
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_SCAN_ROOT_PARENT_IS_SYMLINK"


def test_source_health_rejects_absolute_scan_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    report = run_source_health(repo_root=repo, roots=(str(repo / "ok.py"),))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checked_file_count"] == 0
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_SCAN_ROOT_ABSOLUTE"


def test_source_health_rejects_parent_traversal_scan_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    report = run_source_health(repo_root=repo, roots=("../repo/ok.py",))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checked_file_count"] == 0
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_SCAN_ROOT_PARENT_TRAVERSAL"


def test_source_health_cli_reports_structured_symlinked_scan_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    (repo / "linked.py").symlink_to(repo / "ok.py")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "scripts/source_health.py"),
            "--repo-root",
            str(repo),
            "--json",
            "linked.py",
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
    assert payload["checked_file_count"] == 0
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_SCAN_ROOT_IS_SYMLINK"


def test_source_health_rejects_discovered_symlinked_python_file(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_outside = tmp_path / "outside.py"
    real_outside.write_text("secret = True\n", encoding="utf-8")
    linked_source = repo / "linked_child.py"
    linked_source.symlink_to(real_outside)

    report = run_source_health(repo_root=repo, roots=(".",))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checked_file_count"] == 1
    assert payload["failure_count"] == 1
    assert payload["failures"][0]["path"] == "linked_child.py"
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_FILE_IS_SYMLINK"
