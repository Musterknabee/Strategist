# Next Single-Tenant Slice: Repository Truth SQLite Migration Path Hardening

## Objective

Close the remaining repository-truth evidence gap around SQLite migration metadata. The runtime migration loader already rejects symlinked migration roots and SQL files, but `scripts/repository_truth_check.py` still derived schema-version evidence by globbing `strategy_validator/migrations/sqlite/*.sql` directly.

That meant a symlinked migration root or linked `*.sql` file could influence repository-truth checks without being reported as path-integrity failure.

## Implemented changes

- Added `_safe_sqlite_migration_files(repo_root)` to `scripts/repository_truth_check.py`.
- Repository-truth migration evidence now rejects:
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_IS_SYMLINK`
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_PARENT_IS_SYMLINK`
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_ROOT_NOT_DIRECTORY`
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_IS_SYMLINK`
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_PARENT_IS_SYMLINK`
  - `REPOSITORY_TRUTH_SQLITE_MIGRATION_FILE_NOT_REGULAR`
- Refactored schema-version and migration-tracking checks to consume the validated migration file set instead of directly globbing the filesystem.
- Added constitutional coverage in `tests/constitutional/test_repository_truth_sqlite_migration_path_integrity.py`.
- Added the new constitutional test to the high-gravity `source_health` scope.

## Validation

Validated with focused constitutional checks:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_repository_truth_sqlite_migration_path_integrity.py \
  tests/constitutional/test_repository_truth_docs_path_integrity.py \
  tests/constitutional/test_sqlite_migration_path_integrity.py \
  tests/constitutional/test_migration_truth_repo_root_path_integrity.py \
  tests/constitutional/test_source_health_scan_root_path_integrity.py \
  tests/constitutional/test_repo_archive_path_integrity.py \
  --tb=short
```

Result: `34 passed`.

Validated repository truth and source health gates:

```bash
python scripts/repository_truth_check.py --json
python scripts/source_health.py --json
```

Both reported `PASS`.

## Risk posture

This slice does not alter migration SQL semantics, ledger mutation authority, API behavior, or deployment configuration. It only makes the repository-truth evidence scanner refuse filesystem indirection before trusting migration metadata.
