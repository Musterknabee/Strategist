# Next Slice Ledger: Single-Tenant Env Parent Symlink Hardening

## Objective

Close the remaining deployment-env filesystem-indirection gap for single-tenant readiness tooling.

## Problem

Earlier hardening rejected a directly symlinked `deployment.env`, but an operator could still pass an env file through a symlinked parent directory. That makes token/base-url evidence depend on a path alias outside the reviewed deployment envelope.

The standalone HTTP smoke runner had the same shape and is copied into generated bundles, so it needed a local stdlib-only implementation rather than importing repository helpers.

## Changes

- `strategy_validator/cli/deployment_env_check.py`
  - Parses env files through `absolute_path_preserving_symlink()`.
  - Rejects env files under symlinked parent directories with `ENV_FILE_PARENT_IS_SYMLINK`.

- `strategy_validator/cli/single_tenant_api_smoke.py`
  - Adds standalone symlink-preserving env-file validation.
  - Rejects symlinked `--env-file` paths.
  - Rejects `--env-file` under symlinked parent directories.
  - Rejects non-regular and missing env-file paths with structured error codes.
  - Reuses those checks for both token resolution and base-URL derivation.

- `tests/constitutional/test_single_tenant_deployment_env_check.py`
  - Adds parent-symlink rejection coverage.

- `tests/constitutional/test_single_tenant_api_smoke_token_sources.py`
  - Adds symlinked env-file rejection coverage.
  - Adds parent-symlink rejection coverage.
  - Adds non-regular env-file rejection coverage.
  - Adds CLI JSON `error_code` coverage.

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

Result: `52 passed`.

Additional checks:

```bash
python scripts/source_health.py
python scripts/repository_truth_check.py
python -m compileall -q strategy_validator tests
```

All passed.
