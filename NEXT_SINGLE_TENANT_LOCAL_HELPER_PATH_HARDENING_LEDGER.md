# NEXT_SINGLE_TENANT_LOCAL_HELPER_PATH_HARDENING_LEDGER

## Slice

Harden local single-tenant helper scripts that sit outside the main deployment gates and read/write `deployment.env` or frontend `.env` files directly.

## Why

The main single-tenant bundle, env, preflight, readiness, ledger, provider, signoff, and archive paths now reject symlinked artifacts. The local helper scripts were still weaker:

- `scripts/setup_local_deployment.py` could overwrite `deployment.env` through a symlink.
- `scripts/setup_local_deployment.py` could seed `.env.local` through a symlinked frontend env path.
- `scripts/run_local_api_with_deployment_env.py` could read `deployment.env` through a symlink.
- `scripts/run_preflight_with_deployment_env.py` could read `deployment.env` through a symlink.

These are local convenience entrypoints, but they handle secret-bearing files and bootstrap durable paths, so they should obey the same fail-closed path-integrity posture.

## Changes

- Added shared path-integrity checks to local helper scripts via `scripts._path_integrity`.
- `setup_local_deployment.py` now rejects unsafe:
  - deployment env output path
  - repo-local `.local` output root
  - backup/artifact output roots
  - frontend `.env.local` output
  - frontend `.env.example` input
- `setup_local_deployment.py` applies best-effort `0600` permissions to generated `deployment.env`.
- `run_local_api_with_deployment_env.py` now rejects unsafe `deployment.env` before loading secrets.
- `run_preflight_with_deployment_env.py` now rejects unsafe `deployment.env` before launching preflight.

## Structured failure schema

Path-integrity failures emit:

```json
{
  "schema_version": "local_deployment_helper_path_error/v1",
  "ok": false,
  "code": "...",
  "path": "...",
  "detail": "..."
}
```

Representative codes:

- `SETUP_LOCAL_DEPLOYMENT_ENV_FILE_IS_SYMLINK`
- `SETUP_LOCAL_DEPLOYMENT_OUTPUT_DIR_IS_SYMLINK`
- `SETUP_LOCAL_DEPLOYMENT_WEB_ENV_LOCAL_IS_SYMLINK`
- `SETUP_LOCAL_DEPLOYMENT_WEB_ENV_EXAMPLE_IS_SYMLINK`
- `RUN_LOCAL_API_ENV_FILE_IS_SYMLINK`
- `RUN_PREFLIGHT_ENV_FILE_IS_SYMLINK`

## Tests

Added:

- `tests/constitutional/test_local_deployment_helper_path_integrity.py`

Covered:

- symlinked `deployment.env` overwrite rejection
- symlinked `.local` durable root rejection
- symlinked frontend `.env.local` rejection
- symlinked frontend `.env.example` rejection
- `deployment.env` owner-only permission posture
- local API helper symlinked env-file rejection
- local preflight helper symlinked env-file rejection
