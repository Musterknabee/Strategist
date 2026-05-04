# Next Slice Ledger — Frontend Readiness Claim Path Integrity

## Slice
Harden the opt-in single-tenant frontend readiness claim path so runtime claim loading and claim generation fail closed when claim artifacts are reached through symlinked filesystem paths.

## Changes
- `strategy_validator/application/frontend_readiness_claim.py`
  - Preserves operator-provided claim paths without resolving through symlinks.
  - Rejects symlinked claim artifacts and claim artifacts under symlinked parents.
  - Keeps `frontend_readiness_claimed=false` and `frontend_runtime_reachable=null` on unsafe path evidence.
  - Emits machine-readable `path_integrity` diagnostics.

- `scripts/claim_single_tenant_frontend_readiness.py`
  - Reuses shared script path-integrity helpers.
  - Rejects symlinked claim output paths before running npm/API checks.
  - Rejects claim outputs under symlinked parent directories before writing JSON evidence.
  - Emits `frontend_readiness_claim_path_error/v1` diagnostics and exits with code `2`.

- `tests/constitutional/test_frontend_readiness_claim_path_integrity.py`
  - Covers regular claim acceptance.
  - Covers symlinked runtime claim rejection.
  - Covers runtime claim under symlinked parent rejection.
  - Covers symlinked generator output rejection.
  - Covers generator output under symlinked parent rejection.

## New diagnostic codes
- `FRONTEND_READINESS_CLAIM_PATH_IS_SYMLINK`
- `FRONTEND_READINESS_CLAIM_PATH_PARENT_IS_SYMLINK`
- `FRONTEND_READINESS_CLAIM_OUTPUT_IS_SYMLINK`
- `FRONTEND_READINESS_CLAIM_OUTPUT_PARENT_IS_SYMLINK`

## Result
The backend-only UI facade cannot be upgraded to claimed frontend readiness via symlinked claim artifacts, and the claim generator cannot write evidence through filesystem indirection.
