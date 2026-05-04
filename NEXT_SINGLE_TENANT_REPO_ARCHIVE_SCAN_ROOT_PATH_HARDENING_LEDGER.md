# Next Single-Tenant Repo Archive Scan-Root Path Hardening Ledger

## Slice

Hardened the clean repository archive builder so caller-selected archive scan roots remain repository-relative and symlink-visible.

## Problem

`scripts/package_repo.py` already rejected symlinked repo roots and archive output paths, but `iter_clean_repo_files(..., roots=...)` converted each selected scan root through `Path.resolve()`. That could silently follow a symlinked file or parent directory before archive selection, laundering a caller-selected external path into the clean handoff workflow or hiding the reason an archive root was unsafe.

## Implementation

- Added `_safe_archive_scan_root(repo_root, raw_root)` to `scripts/package_repo.py`.
- Replaced scan-root `Path.resolve()` usage with symlink-preserving validation.
- Rejected archive scan roots that are:
  - absolute paths,
  - parent-traversal paths,
  - symlinked final components,
  - below symlinked parent directories,
  - outside the reviewed repo envelope.
- Added constitutional regression tests to `tests/constitutional/test_repo_archive_path_integrity.py`.
- Added the archive path-integrity test file to the default source-health high-gravity scope.

## Files changed

- `scripts/package_repo.py`
- `scripts/source_health.py`
- `tests/constitutional/test_repo_archive_path_integrity.py`

## Validation

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_repo_archive_path_integrity.py \
  tests/constitutional/test_source_health_scan_root_path_integrity.py \
  tests/constitutional/test_ci_gate_repo_root_path_integrity.py \
  tests/constitutional/test_ui_public_facade_snapshot_assets.py
```

Result: `24 passed`.

Additional gates run:

```bash
python scripts/source_health.py --json
python scripts/source_health.py --repo-owned --json
python scripts/repository_truth_check.py --json
python scripts/migration_truth_check.py --json
python scripts/package_repo.py --check --json
```

All reported `PASS`.

## Operator impact

Clean handoff archive generation remains deterministic, but internally selected archive roots can no longer depend on symlink-following behavior. Unsafe roots fail before any archive is written.
