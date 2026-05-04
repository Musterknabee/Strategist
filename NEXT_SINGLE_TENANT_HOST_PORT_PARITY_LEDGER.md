# Next Single-Tenant Host Port Parity Ledger

## Objective

Close the remaining single-tenant runtime parity gap between Docker Compose,
systemd, deployment env validation, and the API smoke target URL.

## Findings

- The generated Docker Compose template supported `STRATEGY_VALIDATOR_HOST_PORT`.
- The generated API smoke runner already derived its target from
  `STRATEGY_VALIDATOR_HOST_PORT` when no explicit base URL was supplied.
- The generated systemd template still hard-coded `-p 127.0.0.1:8000:8000`.
- The deployment env checker did not validate an operator-supplied
  `STRATEGY_VALIDATOR_HOST_PORT`, so invalid values could pass preflight and
  fail later during container start or smoke.

## Changes

- Added optional host-port validation to
  `strategy_validator/cli/deployment_env_check.py`.
- Added `HOST_PORT_INVALID` as a deployment-blocking env issue.
- Exposed `host_port` and `host_port_configured` in the env-check evidence
  payload.
- Updated the generated systemd template to set
  `Environment=STRATEGY_VALIDATOR_HOST_PORT=8000` and bind
  `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000`.
- Added `STRATEGY_VALIDATOR_HOST_PORT=8000` to `deployment.env.sample`.
- Updated single-tenant deployment docs and backend container docs.
- Added constitutional tests for env validation and generated systemd parity.

## Validation

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_env_check.py tests/constitutional/test_single_tenant_api_smoke_token_sources.py tests/constitutional/test_single_tenant_deployment_bundle.py -q`
- `python -m py_compile strategy_validator/cli/deployment_env_check.py strategy_validator/cli/single_tenant_deployment_bundle.py`

## Boundary

This slice preserves the backend-only single-tenant deployment boundary. It does
not claim frontend readiness, multi-tenant readiness, or SaaS readiness.
