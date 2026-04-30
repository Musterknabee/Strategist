# Next single-tenant helper env-path canonicalization ledger

## Summary

Hardened generated single-tenant helper scripts so custom `STRATEGY_VALIDATOR_ENV_FILE` values are canonicalized to absolute host paths before Docker, smoke, ledger, and evidence commands consume them.

## Risk closed

Several generated helpers self-located bundle defaults, but still accepted caller-relative custom env paths. That could make a command launched from a different working directory pass a different env file to Docker `--env-file`, the smoke runner, or post-deploy child helpers than the operator intended.

## Changes

- `commands/preflight.sh`, `commands/verify-ledger.sh`, `commands/backup-ledger.sh`, and `commands/restore-ledger.sh` now fail early when the env file is missing, canonicalize it to an absolute host path, and export the canonical value before Docker execution.
- `commands/api-smoke.sh` canonicalizes an existing env file before passing it to the packaged or bundled smoke runner.
- `commands/post-deploy-evidence.sh` validates and canonicalizes the env file once, exports the canonical value, and therefore keeps child helpers aligned with the same env file.
- Bundle verification now rejects helper env-path contract drift even if `manifest.json` is regenerated from drifted helper scripts.

## Validation

- Added regression tests for missing helper env canonicalization and missing post-deploy env export.
- Focused single-tenant bundle tests pass under `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.
