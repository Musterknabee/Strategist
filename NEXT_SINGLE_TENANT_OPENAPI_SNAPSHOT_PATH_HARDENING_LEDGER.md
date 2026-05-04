# Next Slice: OpenAPI Snapshot Path-Integrity Hardening

## Summary

Hardened `scripts/openapi_contract_snapshot.py` so OpenAPI contract snapshot verification and generation reject symlinked input/output paths before reading or writing evidence.

## Files changed

- `scripts/openapi_contract_snapshot.py`
- `tests/constitutional/test_openapi_snapshot_path_integrity.py`

## New failure schema

- `openapi_contract_snapshot_path_error/v1`

## New fail-closed codes

- `OPENAPI_SNAPSHOT_IS_SYMLINK`
- `OPENAPI_SNAPSHOT_PARENT_IS_SYMLINK`
- `OPENAPI_SNAPSHOT_OUTPUT_IS_SYMLINK`
- `OPENAPI_SNAPSHOT_OUTPUT_PARENT_IS_SYMLINK`
- `OPENAPI_SNAPSHOT_OUTPUT_NOT_FILE`

## Operator value

The OpenAPI snapshot is release evidence. It now follows the same filesystem-indirection policy as the UI facade snapshot and repo handoff archive tooling: evidence inputs and outputs must be regular paths under the reviewed workspace, not symlinks.
