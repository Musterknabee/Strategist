# Next Single-Tenant Slice: Compose shutdown env contract

## Problem

The generated `commands/compose-up.sh` treated the deployment env file as part of the runtime contract: it failed early when the file was missing, canonicalized custom env and Compose paths, passed the env to Compose via `--env-file`, and exported `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` so service runtime env loading matched interpolation.

`commands/compose-down.sh` still tolerated a missing env file and built its Compose arguments conditionally. That allowed shutdown behavior to depend on the caller's working directory or an absent env file, creating a subtle mismatch from startup for non-default Compose/env paths.

## Change

- Made generated `compose-down.sh` require `STRATEGY_VALIDATOR_ENV_FILE` just like startup.
- Canonicalized and exported the deployment env path before invoking Compose.
- Removed the conditional `args` path and always passes the canonical env file with `--env-file`.
- Extended bundle structural checks to reject `compose-down.sh` drift around env-file guard/canonicalization/export and Compose args.
- Added regression coverage proving refreshed manifests cannot hide a missing `compose-down.sh` env guard.

## Validation

Focused tests cover generated helper contents and regenerated-manifest drift detection. Repository/package/archive gates were rerun after the patch.
