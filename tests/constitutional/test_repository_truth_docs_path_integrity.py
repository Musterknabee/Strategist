from __future__ import annotations

from pathlib import Path

import pytest

from scripts._path_integrity import PathIntegrityError
from scripts.repository_truth_check import _iter_markdown_files, _safe_docs_markdown_root


def _minimal_repo(root: Path) -> Path:
    repo = root / "repo"
    repo.mkdir()
    return repo


def test_repository_truth_docs_scan_rejects_symlinked_docs_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    outside_docs = tmp_path / "outside-docs"
    outside_docs.mkdir()
    (outside_docs / "README.md").write_text("strategy-validator-ghost\n", encoding="utf-8")
    (repo / "docs").symlink_to(outside_docs, target_is_directory=True)

    with pytest.raises(PathIntegrityError) as exc_info:
        _safe_docs_markdown_root(repo)

    assert exc_info.value.code == "REPOSITORY_TRUTH_DOCS_ROOT_IS_SYMLINK"


def test_repository_truth_docs_scan_rejects_non_directory_docs_root(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    (repo / "docs").write_text("not a directory\n", encoding="utf-8")

    with pytest.raises(PathIntegrityError) as exc_info:
        _safe_docs_markdown_root(repo)

    assert exc_info.value.code == "REPOSITORY_TRUTH_DOCS_ROOT_NOT_DIRECTORY"


def test_repository_truth_docs_scan_does_not_follow_nested_docs_symlink(tmp_path: Path) -> None:
    repo = _minimal_repo(tmp_path)
    docs = repo / "docs"
    docs.mkdir()
    (docs / "README.md").write_text("repo docs\n", encoding="utf-8")
    outside_docs = tmp_path / "outside-docs"
    outside_docs.mkdir()
    (outside_docs / "external.md").write_text("tests/does_not_exist.py\n", encoding="utf-8")
    (docs / "linked").symlink_to(outside_docs, target_is_directory=True)

    docs_root = _safe_docs_markdown_root(repo)
    markdown_paths = tuple(path.relative_to(repo).as_posix() for path in _iter_markdown_files(repo, docs_root))

    assert markdown_paths == ("docs/README.md",)
