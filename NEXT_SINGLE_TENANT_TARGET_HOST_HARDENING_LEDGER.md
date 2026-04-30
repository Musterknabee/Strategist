# Next single-tenant target-host hardening ledger

## Scope

Continued the single-tenant production-readiness work from the previous patched archive. This tranche focused on target-host portability and research/advisory auth misconfiguration.

## Changes

- Made generated deployment bundles self-locating for `commands/acceptance.sh` and `commands/post-deploy-evidence.sh`.
- Added `commands/api-smoke.py` to generated bundles as a standard-library fallback runner so API smoke does not require the source checkout or an installed host package.
- Kept `commands/api-smoke.sh` compatible with the packaged `strategy-validator-single-tenant-api-smoke` entrypoint while falling back to the bundled Python runner.
- Tightened deployment env validation so a configured placeholder `STRATEGY_VALIDATOR_RESEARCH_API_TOKEN` is an ERROR, not a warning.
- Hardened production research route auth to reject placeholder research or mutation compatibility tokens before accepting requests.
- Updated deployment acceptance to require `commands/api-smoke.py` in verified bundles.
- Added Docker-image fallbacks for generated acceptance/evidence helpers when `strategy-validator-*` CLIs are not installed on the target host.
- Updated single-tenant deployment docs for the portable smoke fallback and self-locating bundle scripts.

## Validation

Focused constitutional single-tenant tests passed with plugin autoload disabled in the sandbox:

```text
22 passed
```

Validated coverage included bundle generation/checking, deployment env validation, acceptance, evidence, preflight static contract, API smoke script coverage, and runtime token policy.

## Caveat

The sandbox environment still does not represent the full production dependency environment. API import/runtime tests that require the project's declared dependency versions should be run in the intended Python 3.11 + Pydantic v2 environment.
