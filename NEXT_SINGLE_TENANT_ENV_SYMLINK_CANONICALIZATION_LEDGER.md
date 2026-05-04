# Next Slice Ledger: single-tenant env symlink canonicalization

## Intent

Close the remaining symlink bypass in the single-tenant deployment path. The low-level env checker rejected symlinked `deployment.env` files, but higher-level bundle and acceptance gates converted the operator-provided path with `Path.resolve()` before validation. That followed the symlink first and hid the symlink from `Path.is_symlink()`.

## Changes

- Added `absolute_path_preserving_symlink()` in `strategy_validator/cli/deployment_env_check.py`.
  - Produces stable absolute report paths.
  - Does **not** resolve/follow the final symlink target.
- Updated `strategy_validator/cli/single_tenant_deployment_bundle.py` to validate the original env path shape instead of the resolved target.
- Updated `strategy_validator/cli/single_tenant_deployment_acceptance.py` to preserve env symlink visibility through the go/no-go gate.
- Updated `strategy_validator/cli/single_tenant_deployment_evidence.py` so report override paths are not resolved before symlink checks.

## Regression coverage

- `tests/constitutional/test_single_tenant_deployment_bundle.py`
  - bundle generation rejects a symlinked deployment env.
- `tests/constitutional/test_single_tenant_deployment_acceptance.py`
  - acceptance reports `ENV_FILE_IS_SYMLINK` for symlinked deployment env input.
- `tests/constitutional/test_single_tenant_deployment_evidence.py`
  - evidence report overrides reject symlinked JSON report paths.

## Validation

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_env_check.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_api_smoke_token_sources.py \
  tests/constitutional/test_single_tenant_api_smoke_script.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py
```

Result: `36 passed`.

Also passed:

```bash
python scripts/source_health.py
python scripts/repository_truth_check.py
```
