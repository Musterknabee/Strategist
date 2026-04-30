# Production Phase Execution (Sandbox)

## Phase 0 — Convergence and surface repair
Completed in sandbox:
- restored missing validator/projection public exports
- repaired CLI runner registration drift for temporal commands
- repaired star-import helper leakage in queue/pack runner stacks
- repaired incident pack assembly request contract drift
- moved the test suite from collection failure to broad execution

## Phase 1 — Narrowed production slice
Completed in sandbox:
- documented a scoped v1 production boundary in `docs/PRODUCTION_SLICE_V1.md`

## Phase 2 — Runtime boringness
Completed in sandbox:
- added `strategy-validator-migrate`
- added `strategy-validator-api`
- added Dockerfile and .dockerignore
- aligned package metadata with FastAPI runtime and uvicorn deployment entrypoint

## Phase 4 — API mutation hardening
Completed in sandbox:
- added token-based mutation authentication (`STRATEGY_VALIDATOR_API_TOKEN`)
- converted projection rebuild from mutating GET to authenticated POST
- added `/healthz`, `/livez`, `/readyz`

## Remaining work
- complete remaining long-tail test convergence beyond the executed slices
- storage upgrade path beyond single-node SQLite
- frontend dependency pinning / lockfile generation
- stricter UI truthfulness and CI coverage for the Next.js app
- deploy manifests and rollback/backup drills


## Phase 0b — Additional convergence tranche
Completed in sandbox:
- restored API compatibility for `/rebuild/projection-health` while preserving the hardened POST mutation path
- made strategic fusion default time evaluation deterministic to the advisory payload timestamp when `now_utc` is omitted
- repaired missing doctrine drift evidence payload-type constant used by doctrine memory/evidence CLI flows
- validated the repaired slices across constitutional oracle/operator suites and the unit/integration/data-spine/ledger/tribunal suites

## Current validated posture
Validated in sandbox after the tranche above:
- constitutional operator/oracle slice chunks: passing
- unit/integration/ledger/data_spine/pit/scripts/tribunal suites: passing

Known limitation:
- a single full `pytest -q` run was not captured to completion in one shell invocation because the sandbox session output/truncation behavior interrupted the long run, so validation was completed through targeted suite passes instead of one monolithic transcript
