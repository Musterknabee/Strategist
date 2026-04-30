# Next single-tenant slice: systemd runtime-contract verification

## Problem

The generated bundle checker already enforced structural invariants for Docker Compose, but the generated systemd unit was still mostly protected by ordinary manifest digests and source-level tests. A regenerated manifest from a drifted systemd template could therefore pass bundle verification while widening the API bind, changing durable volume names, dropping the deployment env mount, or moving stale-container cleanup before the pre-start env validator.

For a single-tenant host, that is a production risk: systemd is one of the supported target-host envelopes, and it must obey the same loopback, volume, env-file, and fail-before-cleanup contract as Compose.

## Changes

- Added `_verify_generated_systemd_runtime_contract()` in `strategy_validator/cli/single_tenant_deployment_bundle.py`.
- Bundle checks now require exactly one expected systemd runtime token for:
  - `Environment=STRATEGY_VALIDATOR_HOST_PORT=8000`,
  - `EnvironmentFile=/etc/strategy-validator/deployment.env`,
  - the hardened pre-start env-check container,
  - the deployment env-check command,
  - ignored stale-container cleanup,
  - long-lived API container start,
  - ignored stop,
  - loopback-only host-port bind,
  - deployment env mount,
  - ledger and backup volume mounts.
- Bundle checks now reject forbidden systemd forms:
  - non-ignored stale cleanup,
  - non-ignored stop,
  - hard-coded default port bind,
  - non-loopback default bind.
- Bundle checks now validate ordering: deployment env validation must occur before stale-container cleanup, and cleanup before API start.
- Added constitutional tests that refresh the manifest digest after drift, proving the structural checker—not only digest verification—catches systemd bind/order violations.
- Removed a duplicate `mounted_path_policy_ok = False` assignment in `strategy_validator/cli/deployment_env_check.py`.

## Validation

Focused validation passed with pytest plugin autoload disabled for sandbox stability:

```text
23 passed
```

Covered:

- `tests/constitutional/test_single_tenant_deployment_bundle.py`
- `tests/constitutional/test_single_tenant_deployment_env_check.py`
- `tests/constitutional/test_single_tenant_api_smoke_token_sources.py`
