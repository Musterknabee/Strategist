# Next Single-Tenant Container Path Envelope Ledger

## Objective

Close a first-boot deployment gap in the generated single-tenant Docker/systemd envelope: env validation previously accepted any absolute ledger, backup, and artifact path even though generated containers run with a read-only root filesystem and only mount writable durable volumes at `/var/lib/strategy-validator` and `/var/backups/strategy-validator`.

## Changes

- Hardened `strategy_validator/cli/deployment_env_check.py` with a generated-container path policy:
  - `STRATEGY_VALIDATOR_LEDGER_DB_PATH` must be under `/var/lib/strategy-validator`.
  - `STRATEGY_VALIDATOR_ARTIFACT_ROOT` must be under `/var/lib/strategy-validator`.
  - `STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR` must be under `/var/backups/strategy-validator`.
- Added explicit deployment-blocking issue codes:
  - `LEDGER_PATH_OUTSIDE_WRITABLE_VOLUME`
  - `BACKUP_DIR_OUTSIDE_WRITABLE_VOLUME`
  - `ARTIFACT_ROOT_OUTSIDE_WRITABLE_VOLUME`
- Extended safe env-check payload values with:
  - `container_writable_path_policy_ok`
  - `container_writable_roots`
- Updated generated bundle README text and deployment docs to describe the mounted writable path envelope.
- Added constitutional coverage for env files that use absolute-but-unmounted paths such as `/srv/strategy-validator/...`.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_env_check.py tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py tests/constitutional/test_single_tenant_deployment_evidence.py tests/constitutional/test_single_tenant_api_smoke_token_sources.py tests/constitutional/test_single_tenant_api_smoke_script.py`
- `python -m py_compile strategy_validator/cli/deployment_env_check.py strategy_validator/cli/single_tenant_deployment_bundle.py`

## Boundary

This remains backend-only, single-tenant deployment hardening. It does not add frontend readiness, SaaS/multi-tenant isolation, or distributed runtime semantics.
