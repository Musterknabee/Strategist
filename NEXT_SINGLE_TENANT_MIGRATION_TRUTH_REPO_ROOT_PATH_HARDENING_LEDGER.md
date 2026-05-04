# Next Slice: Migration Truth Repo-Root Path Hardening

## Summary

Hardened `scripts/migration_truth_check.py` so explicit `--repo-root` values are rejected when they are symlinked or under symlinked parent directories. The migration truth gate is part of the release evidence chain and should not silently accept filesystem indirection while reporting schema integrity.

## Changed files

- `scripts/migration_truth_check.py`
- `tests/constitutional/test_migration_truth_repo_root_path_integrity.py`

## New fail-closed codes

- `MIGRATION_TRUTH_REPO_ROOT_IS_SYMLINK`
- `MIGRATION_TRUTH_REPO_ROOT_PARENT_IS_SYMLINK`

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_migration_truth_repo_root_path_integrity.py`
- `python scripts/migration_truth_check.py --json`
- `python scripts/source_health.py --json`
- `python scripts/repository_truth_check.py --json`
- `python -m compileall -q strategy_validator scripts tests`
- `python scripts/verify_repo_archive.py ... --json`
