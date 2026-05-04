# Next Single-Tenant Slice: Migration Path Hardening

## Scope

This slice hardens the direct `strategy-validator-migrate` operator primitive so it follows the same durable-path policy as the single-tenant preflight and ledger-ops surfaces.

## Problem

Earlier slices rejected symlinked ledger paths in preflight and ledger backup/restore/verify operations. The migration CLI remained a lower-level bypass: an operator could pass a symlinked `--database-path`, causing SQLite migration writes to follow filesystem indirection before any deployment evidence was created.

## Change

- `strategy_validator/cli/migrate.py`
  - Preserves operator-provided path visibility instead of resolving through symlinks before validation.
  - Rejects a symlinked database path with `MIGRATION_DATABASE_PATH_IS_SYMLINK`.
  - Rejects database paths under symlinked parent directories with `MIGRATION_DATABASE_PATH_PARENT_IS_SYMLINK`.
  - Returns structured `path_integrity` evidence on both success and failure.
  - Fails closed before creating parent directories or opening SQLite when path integrity fails.

- `tests/constitutional/test_migrate_cli.py`
  - Covers normal explicit migration behavior.
  - Covers final-component symlink rejection.
  - Covers symlinked-parent rejection.

## Validation

Validated focused constitutional and single-tenant deployment surfaces:

- `tests/constitutional/test_migrate_cli.py` — 3 passed
- `tests/constitutional/test_ledger_ops_cli.py` — 17 passed
- `tests/constitutional/test_single_tenant_deployment_bundle.py` — 7 passed
- `tests/constitutional/test_single_tenant_deployment_acceptance.py` — 5 passed
- `tests/constitutional/test_single_tenant_deployment_env_check.py` — 4 passed
- `tests/constitutional/test_single_tenant_deployment_evidence.py` — 9 passed
- `tests/constitutional/test_single_tenant_api_smoke_token_sources.py` — 22 passed
- `tests/constitutional/test_single_tenant_api_smoke_script.py` — 1 passed
- `tests/constitutional/test_single_tenant_deployment_preflight.py` — 4 passed

Additional gates:

- `python scripts/source_health.py` — PASS
- `python scripts/repository_truth_check.py` — PASS
- `python -m compileall -q strategy_validator tests` — PASS
- `python scripts/verify_repo_archive.py /mnt/data/Strategist-main-next-slices-migration-path-hardening.zip --repo-root . --json` — PASS

## Operator impact

Direct migrations now fail closed on filesystem indirection before any mutation. This closes the remaining path-integrity bypass between preflight and lower-level migration operations.
