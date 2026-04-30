# Next Single-Tenant Docker Fallback Mount Ledger

## Scope

This slice hardens generated target-host bundle helpers that fall back to Docker when the
`strategy-validator-*` CLIs are not installed directly on the host.

## Problem

The generated `commands/acceptance.sh` and `commands/post-deploy-evidence.sh` previously
mounted the host bundle path back into the container at the same absolute path for multiple
roles:

- bundle directory,
- repo root,
- env-file directory,
- evidence directory.

With default single-tenant usage those paths are often colocated under the generated bundle.
That can produce duplicate Docker mount targets or conflicting read/write modes before any
acceptance or evidence gate runs.

## Change

- `commands/acceptance.sh` now uses host paths for host-installed CLI execution, but Docker
  fallback execution maps to stable in-container paths:
  - `/bundle`
  - `/repo`
  - `/env/<deployment.env basename>`
- `commands/post-deploy-evidence.sh` now separates host arguments from Docker-container
  arguments using an internal `__CONTAINER_ARGS__` sentinel.
- Docker fallback evidence collection now maps:
  - bundle -> `/bundle`
  - repo root -> `/repo`
  - env directory -> `/env`
  - evidence directory -> `/evidence`

## Validation

Focused constitutional tests cover generated helper content and acceptance behavior. Static
compilation also verifies the patched bundle generator remains syntactically valid.
