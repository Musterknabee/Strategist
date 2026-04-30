# Next single-tenant slice: generated Docker hardening drift guard

## Intent

Remove copy/paste drift from the generated single-tenant Docker/systemd envelope and make the bundle checker reject future drift before target-host deployment.

## Changes

- Removed a duplicated `--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m` flag from the generated systemd pre-start env-validation container.
- Added generated Docker hardening count verification to `strategy-validator-single-tenant-bundle --check`.
- The bundle check now validates the expected hardening profile for:
  - `docker-compose.single-tenant.yml`
  - `systemd/strategy-validator.service`
  - `commands/preflight.sh`
  - `commands/verify-ledger.sh`
  - `commands/backup-ledger.sh`
  - `commands/restore-ledger.sh`
  - `commands/acceptance.sh`
  - `commands/post-deploy-evidence.sh`
- Cleaned two harmless but misleading duplicate assignment/call artifacts left by prior generator-style edits.
- Updated deployment docs to state that hardening flag drift is bundle-verification blocking.

## Why this matters

A generated bundle can be digest-consistent yet still encode a bad hardened runtime envelope if the generator itself drifts. This slice makes the checker validate semantic hardening counts, not only file existence and hashes.

## Validation

- `python -m py_compile strategy_validator/cli/single_tenant_deployment_bundle.py strategy_validator/cli/deployment_env_check.py tests/constitutional/test_single_tenant_deployment_bundle.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_bundle.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_env_check.py tests/constitutional/test_single_tenant_deployment_acceptance.py tests/constitutional/test_single_tenant_api_smoke_token_sources.py`
