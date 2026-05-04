# Next Slice: Single-Tenant Report/Output Path Hardening

## Scope

This slice tightens operator-facing single-tenant deployment commands so evidence, bundle, acceptance, and preflight paths preserve symlink visibility before read/write operations.

## Implemented changes

- Added shared path helpers in `strategy_validator/cli/deployment_env_check.py`:
  - `symlink_components_preserving_path()`
  - `has_symlink_component()`
- Hardened `strategy_validator/cli/single_tenant_deployment_bundle.py`:
  - rejects symlinked bundle output directories before generation
  - rejects symlinked bundle directories before verification
  - avoids collecting generated-file digests through symlinked output roots
- Hardened `strategy_validator/cli/single_tenant_deployment_acceptance.py`:
  - preserves symlink visibility for `--bundle-dir`
  - emits a structured failure for symlinked bundle directories
  - refuses to write summary markdown through a symlinked path
- Hardened `strategy_validator/cli/single_tenant_deployment_evidence.py`:
  - preserves symlink visibility for `--evidence-dir`
  - refuses symlinked evidence roots before reading report files
  - reports non-regular evidence report paths as structured failures instead of raising while hashing
  - refuses to write manifest/summary outputs through symlinked paths
- Hardened `strategy_validator/cli/single_tenant_preflight.py`:
  - reuses shared symlink-component helper
  - refuses to write summary markdown through symlinked output paths and records a machine-readable failure

## Tests added

- Bundle generation rejects symlinked output directories.
- Bundle check rejects symlinked bundle directories.
- Acceptance rejects symlinked bundle directories.
- Acceptance rejects symlinked markdown output paths.
- Evidence rejects symlinked evidence directories.
- Evidence reports directory/non-regular report paths as failures.
- Evidence rejects symlinked manifest output paths.
- Preflight rejects symlinked summary output paths.

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
# 46 passed

python scripts/source_health.py
# PASS

python scripts/repository_truth_check.py
# PASS

python -m compileall -q strategy_validator \
  tests/constitutional/test_single_tenant_deployment_bundle.py \
  tests/constitutional/test_single_tenant_deployment_acceptance.py \
  tests/constitutional/test_single_tenant_deployment_evidence.py \
  tests/constitutional/test_single_tenant_deployment_preflight.py
# PASS
```
