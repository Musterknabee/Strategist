# Next single-tenant smoke port alignment ledger

## Slice objective

Keep post-start API smoke aligned with the generated Docker Compose host-port binding.

## Problem found

The generated Compose template supports `STRATEGY_VALIDATOR_HOST_PORT`, but the smoke helper path defaulted to `http://127.0.0.1:8000`. A valid deployment using a non-default host port could start successfully and then fail smoke/evidence collection against the wrong port.

## Changes

- Added `resolve_smoke_base_url(...)` to the standalone smoke runner.
- Smoke now resolves target URL in this order:
  1. explicit `--base-url`,
  2. `STRATEGY_VALIDATOR_BASE_URL` environment variable,
  3. `STRATEGY_VALIDATOR_BASE_URL` from `deployment.env`,
  4. `STRATEGY_VALIDATOR_HOST_PORT` environment variable,
  5. `STRATEGY_VALIDATOR_HOST_PORT` from `deployment.env`,
  6. `http://127.0.0.1:8000`.
- Invalid derived ports fail closed.
- Generated `commands/api-smoke.sh` no longer injects a hard-coded 8000 base URL.
- Generated post-deploy evidence no longer masks env-file port derivation with a hard-coded base URL.

## Validation

- Focused smoke URL/token tests pass with plugin autoload disabled.
- Focused deployment bundle tests pass with plugin autoload disabled.
- `py_compile` passes for patched modules/tests.
