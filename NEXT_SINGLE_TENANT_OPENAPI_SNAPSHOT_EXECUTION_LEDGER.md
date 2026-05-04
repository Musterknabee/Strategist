# Next Slice Ledger: OpenAPI Snapshot Execution & Drift Reconciliation

## Objective

Close the OpenAPI snapshot gate regression where `scripts/openapi_contract_snapshot.py` was safe when imported by pytest but failed when executed directly by CI/local operators.

## Findings

- `.github/workflows/ci.yml` invokes the tool directly with:
  - `python scripts/openapi_contract_snapshot.py --check`
- After the path-integrity hardening slice, the script imported `scripts._path_integrity` without first placing the repository root on `sys.path`.
- Direct execution therefore failed with `ModuleNotFoundError: No module named 'scripts'`.
- Once direct execution was restored, the OpenAPI snapshot also showed real drift from the current FastAPI app routes.

## Changes

- Updated `scripts/openapi_contract_snapshot.py` to bootstrap the repository root onto `sys.path` before importing `scripts._path_integrity`.
- Regenerated `docs/architecture/openapi.snapshot.json` from the current `strategy_validator.api.app.create_app().openapi()` payload.
- Added a regression test that executes the script the same way CI does:
  - `python scripts/openapi_contract_snapshot.py --check`

## Guardrail

The regression test prevents future path-integrity helper imports from becoming import-only/test-only safe while breaking direct script execution.

## Validation

- `tests/constitutional/test_openapi_snapshot_contract.py`
- `tests/constitutional/test_openapi_snapshot_path_integrity.py`
- `scripts/openapi_contract_snapshot.py --check`
