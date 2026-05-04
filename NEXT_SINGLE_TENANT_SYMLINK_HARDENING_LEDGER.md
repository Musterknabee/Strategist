# Next Single-Tenant Symlink Hardening Ledger

## Slice

Harden the single-tenant deployment handoff against symlink substitution across the private env file, generated deployment bundle, and repo-asset acceptance path.

## Why

The previous deployment evidence hardening rejected symlinked evidence reports. The same fail-closed posture should apply before boot and acceptance:

- `deployment.env` contains bearer-token material and must be a private regular file, not a redirect through a symlink.
- generated bundle members must be regular files so their manifest digests seal the actual operator artifact, not a target outside the bundle.
- source repo assets carried into `repo-assets.manifest.json` and acceptance checks must reject symlinks rather than hashing through them.

## Code changes

- `strategy_validator/cli/deployment_env_check.py`
  - Rejects symlinked env files with `ENV_FILE_IS_SYMLINK` before parsing or permission checks.

- `strategy_validator/cli/single_tenant_deployment_bundle.py`
  - Adds generated-file shape verification for every required bundle member.
  - Rejects symlinked or non-regular generated files.
  - Rejects symlinked manifest-listed files before hashing.
  - Omits symlinked paths from generated file digest collection.
  - Records `is_symlink` in `repo-assets.manifest.json` and fails manifest verification when required repo assets are symlinked.

- `strategy_validator/cli/single_tenant_deployment_acceptance.py`
  - Rejects symlinked repo assets during acceptance checks.
  - Requires generated bundle files to be regular files, not just existing paths.

## Tests

Added regression coverage for:

- symlinked deployment env files
- symlinked generated bundle files
- symlinked repo assets in bundle source manifests
- symlinked repo assets in acceptance checks

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

Result: `33 passed`

```bash
python scripts/source_health.py
python scripts/repository_truth_check.py
```

Result: both PASS.
