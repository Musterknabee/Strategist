# Next Single-Tenant Slice: Compose Env-File Parity

## Summary

This slice closes a Docker Compose parity bug in the generated single-tenant handoff bundle.
`commands/compose-up.sh` already allowed `STRATEGY_VALIDATOR_ENV_FILE` to point at a non-default env file and passed that file to Compose with `--env-file`, but the generated Compose service still loaded `./deployment.env` as the container runtime `env_file`.
That allowed validation/interpolation to use one env file while the API container received another.

## Changes

- Changed generated `docker-compose.single-tenant.yml` to use `${STRATEGY_VALIDATOR_COMPOSE_ENV_FILE:-./deployment.env}` for service `env_file`.
- Changed `commands/compose-up.sh` and `commands/compose-down.sh` to export `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE="${STRATEGY_VALIDATOR_ENV_FILE}"` before invoking Compose.
- Extended bundle structural checks to reject Compose runtime env-file drift and lifecycle helpers that omit the env-file export.
- Added constitutional tests for regenerated-manifest drift in both Compose file and lifecycle helper.
- Updated deployment docs to explain that the helper keeps Compose interpolation and container runtime env aligned.

## Risk Reduced

A non-default `STRATEGY_VALIDATOR_ENV_FILE` can no longer silently validate and interpolate one env file while the API container loads `./deployment.env` at runtime.
