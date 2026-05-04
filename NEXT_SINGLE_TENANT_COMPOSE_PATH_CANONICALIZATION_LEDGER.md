# Next Single-Tenant Compose Path Canonicalization Ledger

## Slice objective

Close a target-host Compose lifecycle mismatch where custom relative
`STRATEGY_VALIDATOR_ENV_FILE` or `STRATEGY_VALIDATOR_COMPOSE_FILE` values could
be validated from one caller-relative location while Docker Compose consumed a
separate relative path for interpolation or service `env_file` loading.

## Production risk addressed

The generated `commands/compose-up.sh` already aligned Compose interpolation and
container runtime env loading via `--env-file` and
`STRATEGY_VALIDATOR_COMPOSE_ENV_FILE`. However, when an operator supplied custom
relative paths, those values remained caller-relative at the Compose invocation
boundary. That made the deployment sensitive to the caller's current working
directory and could reintroduce env-file divergence despite the previous parity
fix.

## Changes

- `commands/compose-up.sh` now canonicalizes the operator env file and Compose
  file to absolute host paths after existence checks.
- `commands/compose-down.sh` now canonicalizes the Compose file and, when
  present, the env file before passing them to Compose.
- Bundle structural verification now requires the generated Compose lifecycle
  helpers to preserve env/Compose path canonicalization.
- Constitutional tests simulate regenerated-manifest drift and verify the bundle
  checker rejects missing canonicalization.
- Deployment docs now describe the absolute-path lifecycle contract for custom
  env/Compose file paths.

## Validation

Focused tests were run with plugin autoload disabled for sandbox determinism:

```text
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/constitutional/test_single_tenant_deployment_bundle.py
16 passed
```

Repository/package/archive gates were run after the patch and passed; see the
turn summary for archive digest and full gate list.
