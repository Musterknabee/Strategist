from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.environment_check import run_environment_check
from scripts.repository_truth_check import run_repository_truth_check
from scripts.source_health import run_source_health

REPO_ROOT = Path(__file__).resolve().parents[2]


def _symlink_to_repo(tmp_path: Path) -> Path:
    link = tmp_path / "repo-link"
    link.symlink_to(REPO_ROOT, target_is_directory=True)
    return link


def test_source_health_rejects_symlinked_repo_root(tmp_path: Path) -> None:
    report = run_source_health(repo_root=_symlink_to_repo(tmp_path), roots=("scripts/source_health.py",))

    assert report.status == "FAIL"
    assert report.checked_file_count == 0
    assert report.failures[0].error_type == "SOURCE_HEALTH_REPO_ROOT_IS_SYMLINK"


def test_repository_truth_check_rejects_symlinked_repo_root(tmp_path: Path) -> None:
    report = run_repository_truth_check(repo_root=_symlink_to_repo(tmp_path))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checks"] == [
        {
            "name": "repo_root_path_integrity",
            "status": "FAIL",
            "detail": payload["checks"][0]["detail"],
        }
    ]
    assert "REPOSITORY_TRUTH_REPO_ROOT_IS_SYMLINK" in payload["checks"][0]["detail"]


def test_environment_check_rejects_symlinked_repo_root_before_dependency_checks(tmp_path: Path) -> None:
    report = run_environment_check(required_distributions=(), repo_root=_symlink_to_repo(tmp_path))

    payload = report.to_payload()
    assert payload["status"] == "FAIL"
    assert payload["checks"] == [
        {
            "name": "repo_root_path_integrity",
            "status": "FAIL",
            "detail": payload["checks"][0]["detail"],
        }
    ]
    assert "ENVIRONMENT_CHECK_REPO_ROOT_IS_SYMLINK" in payload["checks"][0]["detail"]
    assert all(not check["name"].startswith("distribution:") for check in payload["checks"])


def test_source_health_cli_reports_structured_symlinked_repo_root(tmp_path: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "scripts/source_health.py",
            "--repo-root",
            str(_symlink_to_repo(tmp_path)),
            "--json",
            "scripts/source_health.py",
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
    assert payload["failures"][0]["error_type"] == "SOURCE_HEALTH_REPO_ROOT_IS_SYMLINK"
