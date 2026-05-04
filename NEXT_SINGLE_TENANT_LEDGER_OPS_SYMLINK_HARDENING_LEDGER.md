# Next Single-Tenant Ledger Ops Symlink Hardening Ledger

## Objective

Harden the direct `strategy-validator-ledger-ops` backup, restore, and integrity verification path so operator break-glass commands cannot read, hash, preserve, or restore SQLite ledger artifacts through filesystem symlinks.

This closes a lower-layer gap after the single-tenant preflight/env/bundle/evidence commands were hardened: an operator could still bypass those higher-level gates by invoking `ledger_ops` directly.

## Files changed

- `strategy_validator/cli/ledger_ops.py`
- `tests/constitutional/test_ledger_ops_cli.py`

## Behavior added

`ledger_ops` now preserves symlink visibility instead of resolving through symlinked paths before validation.

Fail-closed path checks now cover:

- source ledger database used for backup,
- backup output directory,
- restore source backup path,
- restore destination database path,
- pre-restore backup directory used before overwrite,
- combined `verify-integrity` evidence hashing.

Structured error codes include:

- `LEDGER_DATABASE_PATH_IS_SYMLINK`
- `LEDGER_DATABASE_PATH_PARENT_IS_SYMLINK`
- `LEDGER_BACKUP_DIR_IS_SYMLINK`
- `LEDGER_BACKUP_DIR_PARENT_IS_SYMLINK`
- `LEDGER_RESTORE_BACKUP_PATH_IS_SYMLINK`
- `LEDGER_RESTORE_DESTINATION_PATH_IS_SYMLINK`
- `LEDGER_PRE_RESTORE_BACKUP_DIR_IS_SYMLINK`

## Evidence semantics

`verify_ledger()` and `verify_operator_action_journal()` now include `path_integrity` in their payloads. When the configured ledger DB path is symlinked, they return `ok=false` and do not run chain verification through the symlink.

`verify_ledger_integrity()` now withholds `database_sha256` unless ledger path integrity is explicitly clean. This avoids evidence packs recording a digest for a symlink-followed database.

## Regression tests added

- Backup rejects symlinked database path.
- Backup rejects symlinked backup directory.
- Restore rejects symlinked backup source.
- Restore rejects symlinked destination path.
- Restore rejects symlinked pre-restore backup directory.
- `verify-integrity` rejects a symlinked database and emits no DB digest.
- CLI `verify-integrity --json` exits non-zero for a symlinked database.

## Validation

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_env_check.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_api_smoke_token_sources.py \
  tests/constitutional/test_single_tenant_api_smoke_script.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py \
  tests/constitutional/test_ledger_ops_cli.py
```

Result: `69 passed`.

Additional checks:

```bash
python scripts/source_health.py
python scripts/repository_truth_check.py
python -m compileall -q strategy_validator tests
```

All passed.
