# Next single-tenant slice: acceptance env-file canonicalization

## Summary

The generated `commands/acceptance.sh` helper is now covered by the same env-file path contract as the other target-host helpers.

## Problem

Most generated helpers already failed early when `STRATEGY_VALIDATOR_ENV_FILE` was missing and canonicalized custom relative env paths before invoking Docker or local CLIs. `commands/acceptance.sh` still derived host/container arguments from the env path without an explicit file guard or exported absolute path. That made acceptance the odd helper out and left room for caller-relative path drift between local CLI execution and Docker fallback execution.

## Change

- `commands/acceptance.sh` now fails early when the env file is missing.
- It canonicalizes `STRATEGY_VALIDATOR_ENV_FILE` to an absolute host path.
- It exports the canonical env path before choosing local CLI or Docker fallback.
- Bundle verification now treats acceptance env-path canonicalization as a generated helper contract.
- Constitutional tests simulate a regenerated manifest from a drifted `acceptance.sh` and verify the structural checker rejects it.

## Scope

Backend-only single-tenant deployment helper hardening. No frontend, public SaaS, or multi-tenant readiness claim is made.
