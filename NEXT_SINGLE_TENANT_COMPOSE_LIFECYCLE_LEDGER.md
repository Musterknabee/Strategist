# Next single-tenant production hardening: Compose lifecycle helper contract

## Problem

The generated Docker Compose file exposes the API via:

```yaml
ports:
  - "127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000"
```

However, Docker Compose interpolation is not sourced from a service `env_file:`
stanza. A single-tenant operator could correctly set
`STRATEGY_VALIDATOR_HOST_PORT` in `deployment.env`, run raw
`docker compose -f docker-compose.single-tenant.yml up -d`, and still bind the
default port. That would break the intended parity between Compose, API smoke,
and env validation.

## Changes

- Added generated `commands/compose-up.sh`.
  - Self-locates the bundle root.
  - Defaults to the bundle-local `deployment.env` and Compose file.
  - Runs `strategy-validator-deployment-env-check --require-valid` inside a
    short-lived hardened container before starting the API.
  - Starts Compose with `--env-file "${STRATEGY_VALIDATOR_ENV_FILE}"` so
    host-port interpolation honors the deployment env file.
- Added generated `commands/compose-down.sh`.
  - Uses the same bundle-local Compose/env defaults.
  - Passes `--env-file` when the env file is present.
- Added bundle-level Compose lifecycle contract verification.
  - Missing `--env-file` in `compose-up.sh` is deployment-blocking.
  - Missing pre-start env validation in `compose-up.sh` is deployment-blocking.
  - Compose helper path drift is rejected even if the manifest was regenerated
    from drifted helper files.
- Updated acceptance required bundle files.
- Updated deployment docs and generated bundle README.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_bundle.py tests/constitutional/test_single_tenant_deployment_acceptance.py tests/constitutional/test_single_tenant_deployment_env_check.py`
- `python -m py_compile strategy_validator/cli/single_tenant_deployment_bundle.py strategy_validator/cli/single_tenant_deployment_acceptance.py`

## Scope

This is backend-only, single-tenant deployment hardening. It does not claim
frontend, public SaaS, or multi-tenant readiness.
