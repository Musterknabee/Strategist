# Next Slice: Runtime Ledger Path Hardening

## Objective

Close the final low-level ledger path bypass left after the single-tenant preflight,
migration, and ledger-ops path-hardening slices.

The durable runtime append-only ledger resolver must fail closed before SQLite can
open a symlinked database path or a database path beneath a symlinked parent
component.

## Changes

- Hardened `strategy_validator/ledger/_append_only.py`:
  - Added symlink-aware runtime ledger path integrity checks.
  - Rejected symlinked `STRATEGY_VALIDATOR_LEDGER_DB_PATH` final components with
    `LEDGER_DATABASE_PATH_IS_SYMLINK`.
  - Rejected symlinked parent components with
    `LEDGER_DATABASE_PATH_PARENT_IS_SYMLINK`.
  - Enforced these checks inside `resolve_database_path()` before runtime reads,
    writes, migrations, or SQLite connection creation.

- Preserved higher-level CLI evidence semantics:
  - `strategy_validator/cli/migrate.py` still returns structured migration
    failure payloads with `MIGRATION_DATABASE_PATH_IS_SYMLINK` and
    `MIGRATION_DATABASE_PATH_PARENT_IS_SYMLINK` instead of leaking a raw runtime
    exception.
  - `strategy_validator/cli/ledger_ops.py` still returns/raises
    operation-specific path-integrity errors such as
    `LEDGER_RESTORE_DESTINATION_PATH_IS_SYMLINK`.

- Added constitutional coverage:
  - `tests/constitutional/test_runtime_ledger_path_integrity.py`

## Validation

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_runtime_ledger_path_integrity.py \
  tests/constitutional/test_migrate_cli.py \
  tests/constitutional/test_ledger_ops_cli.py \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_env_check.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_api_smoke_token_sources.py \
  tests/constitutional/test_single_tenant_api_smoke_script.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py
# 75 passed
```

```bash
python scripts/source_health.py --json
# PASS
python scripts/repository_truth_check.py --json
# PASS
python -m compileall -q strategy_validator tests
# PASS
```

## Operator impact

The runtime ledger authority path now has the same fail-closed symlink posture as
the deployment preflight, migration CLI, and backup/restore CLI. An operator can
no longer bypass deployment checks by setting `STRATEGY_VALIDATOR_LEDGER_DB_PATH`
directly to a symlinked SQLite path and letting the live API/runtime follow it.
