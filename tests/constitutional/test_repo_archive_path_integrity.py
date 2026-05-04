from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from scripts.package_repo import UnsafeArchiveOutputError, build_clean_repo_zip
from scripts.verify_repo_archive import verify_clean_repo_archive


def _minimal_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("repo\n", encoding="utf-8")
    (repo / "scripts").mkdir()
    (repo / "scripts" / "tool.py").write_text("print('ok')\n", encoding="utf-8")
    return repo


def _valid_zip(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED) as archive:
        info = zipfile.ZipInfo("README.md")
        info.date_time = (1980, 1, 1, 0, 0, 0)
        info.external_attr = 0o644 << 16
        archive.writestr(info, b"repo\n")


def test_package_repo_rejects_symlinked_archive_output(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_output = tmp_path / "real-output.zip"
    symlink_output = tmp_path / "handoff.zip"
    symlink_output.symlink_to(real_output)

    with pytest.raises(UnsafeArchiveOutputError, match="archive output path is a symlink"):
        build_clean_repo_zip(repo_root=repo, output_path=symlink_output)

    assert not real_output.exists()


def test_package_repo_rejects_archive_output_under_symlinked_parent(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    with pytest.raises(UnsafeArchiveOutputError, match="symlinked parent directories"):
        build_clean_repo_zip(repo_root=repo, output_path=linked_parent / "handoff.zip")

    assert not (real_parent / "handoff.zip").exists()


def test_package_repo_rejects_non_regular_archive_output(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    output_dir = tmp_path / "handoff.zip"
    output_dir.mkdir()

    with pytest.raises(UnsafeArchiveOutputError, match="not a regular file"):
        build_clean_repo_zip(repo_root=repo, output_path=output_dir)


def test_verify_repo_archive_rejects_symlinked_archive_input(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_archive = tmp_path / "real.zip"
    _valid_zip(real_archive)
    linked_archive = tmp_path / "linked.zip"
    linked_archive.symlink_to(real_archive)

    report = verify_clean_repo_archive(linked_archive, repo_root=repo)

    assert report.status == "FAIL"
    assert [failure.name for failure in report.failures] == ["archive_path_integrity"]
    assert report.archive_sha256 is None


def test_verify_repo_archive_rejects_archive_input_under_symlinked_parent(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    real_archive = real_parent / "archive.zip"
    _valid_zip(real_archive)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)

    report = verify_clean_repo_archive(linked_parent / "archive.zip", repo_root=repo)

    assert report.status == "FAIL"
    assert [failure.name for failure in report.failures] == ["archive_path_integrity"]
    assert report.archive_sha256 is None


def test_verify_repo_archive_rejects_non_regular_archive_input(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    archive_dir = tmp_path / "archive.zip"
    archive_dir.mkdir()

    report = verify_clean_repo_archive(archive_dir, repo_root=repo)

    assert report.status == "FAIL"
    assert [failure.name for failure in report.failures] == ["archive_regular_file"]
    assert report.archive_sha256 is None


def test_package_repo_rejects_symlinked_repo_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    linked_repo = tmp_path / "linked-repo"
    linked_repo.symlink_to(repo, target_is_directory=True)
    output = tmp_path / "handoff.zip"

    with pytest.raises(UnsafeArchiveOutputError, match="repo root path is a symlink"):
        build_clean_repo_zip(repo_root=linked_repo, output_path=output)

    assert not output.exists()


def test_package_repo_rejects_repo_root_under_symlinked_parent(tmp_path: Path) -> None:
    real_parent = tmp_path / "real-parent"
    real_parent.mkdir()
    repo = _minimal_repo(real_parent)
    linked_parent = tmp_path / "linked-parent"
    linked_parent.symlink_to(real_parent, target_is_directory=True)
    output = tmp_path / "handoff.zip"

    with pytest.raises(UnsafeArchiveOutputError, match="repo root path has symlinked parent"):
        build_clean_repo_zip(repo_root=linked_parent / repo.name, output_path=output)

    assert not output.exists()


def test_verify_repo_archive_rejects_symlinked_repo_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    archive = tmp_path / "archive.zip"
    _valid_zip(archive)
    linked_repo = tmp_path / "linked-repo"
    linked_repo.symlink_to(repo, target_is_directory=True)

    report = verify_clean_repo_archive(archive, repo_root=linked_repo)

    assert report.status == "FAIL"
    assert [failure.name for failure in report.failures] == ["repo_root_path_integrity"]
    assert report.expected_file_count == 0
    assert report.archive_sha256 is None


def test_package_repo_rejects_symlinked_archive_scan_root_file(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    outside = tmp_path / "outside.py"
    outside.write_text("secret = True\n", encoding="utf-8")
    linked = repo / "linked.py"
    linked.symlink_to(outside)

    with pytest.raises(UnsafeArchiveOutputError, match="archive scan root path is a symlink"):
        build_clean_repo_zip(repo_root=repo, output_path=None, roots=("linked.py",))


def test_package_repo_rejects_archive_scan_root_under_symlinked_parent(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    outside_dir = tmp_path / "outside-src"
    outside_dir.mkdir()
    (outside_dir / "payload.py").write_text("secret = True\n", encoding="utf-8")
    linked_dir = repo / "linked-src"
    linked_dir.symlink_to(outside_dir, target_is_directory=True)

    with pytest.raises(UnsafeArchiveOutputError, match="archive scan root path has symlinked parent"):
        build_clean_repo_zip(repo_root=repo, output_path=None, roots=("linked-src/payload.py",))


def test_package_repo_rejects_absolute_archive_scan_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    with pytest.raises(UnsafeArchiveOutputError, match="archive scan root must be repository-relative"):
        build_clean_repo_zip(repo_root=repo, output_path=None, roots=(str(repo / "README.md"),))


def test_package_repo_rejects_parent_traversal_archive_scan_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)

    with pytest.raises(UnsafeArchiveOutputError, match="archive scan root must not contain parent traversal"):
        build_clean_repo_zip(repo_root=repo, output_path=None, roots=("../repo/README.md",))
