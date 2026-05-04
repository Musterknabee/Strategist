# Next Slice Ledger — Repository Truth Docs Path Hardening

## Slice

Hardened the repository truth gate's implicit documentation scan root.

## Problem

`scripts/repository_truth_check.py` scans repository documentation to verify that documented console commands and documented pytest paths match the checked-out source tree. The previous implementation used `Path.rglob("*.md")` starting at `docs/`. On supported Python versions, a symlinked `docs/` root can be traversed, allowing markdown outside the reviewed repository envelope to influence repository truth evidence.

## Change

- Added a symlink-preserving `docs/` scan-root validator.
- Added machine-readable failure codes:
  - `REPOSITORY_TRUTH_DOCS_ROOT_IS_SYMLINK`
  - `REPOSITORY_TRUTH_DOCS_ROOT_PARENT_IS_SYMLINK`
  - `REPOSITORY_TRUTH_DOCS_ROOT_NOT_DIRECTORY`
- Replaced `Path.rglob("*.md")` with an `os.walk` scanner that prunes symlinked nested documentation directories and ignores symlinked markdown files.
- Added constitutional regression coverage for symlinked docs roots, non-directory docs roots, and nested symlink traversal prevention.
- Added the new constitutional test to the high-gravity source-health scope.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_repository_truth_docs_path_integrity.py tests/constitutional/test_ci_gate_repo_root_path_integrity.py tests/constitutional/test_repo_archive_path_integrity.py tests/constitutional/test_source_health_scan_root_path_integrity.py`
- `python scripts/source_health.py --json`
- `python scripts/source_health.py --repo-owned --json`
- `python scripts/repository_truth_check.py --json`
- `python scripts/migration_truth_check.py --json`
- `python scripts/package_repo.py --check --json`
- `python scripts/package_repo.py --output <zip> --json`
- `python scripts/verify_repo_archive.py <zip> --json`
