# Next Slice Ledger: SQLite Runtime Migration + Source Health Symlink Hardening

## Status

Implemented and validated.

## Slice summary

This slice closes two adjacent path-integrity gaps in the single-tenant evidence chain:

1. The runtime SQLite migration loader no longer discovers or executes SQL through symlinked migration module paths, symlinked `sqlite/` roots, symlinked parent directories, or symlinked `.sql` files.
2. `scripts/source_health.py` no longer parses discovered Python source files that are symlinks. Scan roots were already protected; this extends the protection to files found during recursive source discovery.

## Why this matters

The release and handoff gates are intended to prove the repository under review, not an external tree reached through filesystem indirection. A symlinked migration file can execute SQL that is not actually part of the reviewed source envelope. A symlinked discovered Python file can cause the source-health gate to parse external source and produce misleading evidence.

## Runtime migration hardening

Changed `strategy_validator/migrations/__init__.py` to:

- preserve symlink visibility instead of using `Path(__file__).resolve().parent / "sqlite"`;
- raise `SQLiteMigrationPathError` with machine-readable codes;
- reject symlinked migration module paths;
- reject symlinked `strategy_validator/migrations/sqlite` roots;
- reject symlinked parent directories;
- reject non-directory migration roots;
- reject symlinked SQL migration files;
- reject non-regular SQL migration paths.

Changed `scripts/migration_truth_check.py` to report runtime migration path-integrity failures as structured migration truth failures instead of crashing.

## Source-health hardening

Changed `scripts/source_health.py` to:

- inspect every discovered Python source path for symlink components before reading it;
- report `SOURCE_HEALTH_FILE_IS_SYMLINK` for symlinked discovered `.py` files;
- report `SOURCE_HEALTH_FILE_PARENT_IS_SYMLINK` for discovered files under symlinked parents;
- avoid counting rejected symlinked source files as checked files.

## Tests added or extended

- `tests/constitutional/test_sqlite_migration_path_integrity.py`
- `tests/constitutional/test_source_health_scan_root_path_integrity.py`

## Validation commands

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_sqlite_migration_path_integrity.py \
  tests/constitutional/test_migration_truth_repo_root_path_integrity.py \
  tests/constitutional/test_packaging_sqlite_migrations.py \
  tests/constitutional/test_source_health_scan_root_path_integrity.py \
  tests/constitutional/test_repository_truth_docs_path_integrity.py \
  tests/constitutional/test_repo_archive_path_integrity.py \
  --tb=short
```

Result: `32 passed`.

Additional gates run:

```bash
python scripts/source_health.py --json
python scripts/source_health.py --repo-owned --json
python scripts/migration_truth_check.py --json
python scripts/repository_truth_check.py --json
python scripts/package_repo.py --check --json
```

All passed.
