# Next slice: deployment readiness support-root path integrity

## Objective

Close the remaining deployment-readiness gap where support roots were judged mainly by writability. The runtime ledger path was already hardened, but `STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR` and `STRATEGY_VALIDATOR_ARTIFACT_ROOT` could still be symlinked or live under symlinked parents and appear ready.

## Changes

- Hardened `strategy_validator/validator/readiness.py`.
- Added symlink-preserving support-root path checks.
- Added machine-readable readiness checks:
  - `backup_root_path_integrity`
  - `artifact_root_path_integrity`
- Writability checks now run only after path integrity passes.
- Added fail-closed blocker codes:
  - `BACKUP_ROOT_IS_SYMLINK`
  - `BACKUP_ROOT_PARENT_IS_SYMLINK`
  - `ARTIFACT_ROOT_IS_SYMLINK`
  - `ARTIFACT_ROOT_PARENT_IS_SYMLINK`

## Tests

Expanded `tests/constitutional/test_deployment_readiness_tier.py` with regression coverage for:

- symlinked backup root rejection
- artifact root under symlinked parent rejection

## Validation

Targeted validation run:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_deployment_readiness_tier.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py \
  tests/constitutional/test_runtime_ledger_path_integrity.py \
  tests/constitutional/test_ledger_ops_cli.py
```

Result: `28 passed`.

Repository health and archive verification were run after this slice.
