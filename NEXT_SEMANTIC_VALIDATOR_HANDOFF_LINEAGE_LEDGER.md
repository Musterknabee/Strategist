# NEXT Semantic Validator Handoff Lineage Ledger

## Completed vertical slice

Implemented a read-only semantic validator handoff lineage/continuity verifier.

## Backend

- Added `strategy_validator/application/ui_semantic_validator_handoff_lineage.py`.
- Added `GET /ui/semantic-validator-handoff/lineage`.
- Added `GET /ui/semantic-validator-handoff/lineage/latest`.
- Registered the routes in the UI public facade as read-plane routes with schema `ui_semantic_validator_handoff_lineage/v1`.
- Regenerated OpenAPI and UI facade contract snapshots.

## Frontend

- Added typed API contracts for lineage chains/components/payloads.
- Added `useUiSemanticValidatorHandoffLineage` hook.
- Added `/semantic-validator-handoff-lineage` terminal cockpit page.
- Added rail navigation, command-palette navigation, G-chord path, and route-query refresh wiring.
- Added demo-mode payloads for the new read-plane paths.

## Tests and validation

- Added application tests for ready, broken-checksum, and incomplete lineage states.
- Added API route regression tests for lineage and latest endpoints.
- Updated frontend route/query/command test expectations.
- Verified targeted backend tests: `pytest -q tests/application/test_ui_semantic_validator_handoff_lineage.py`.
- Verified route behavior directly with `TestClient(create_app())` because pytest collection for API route tests is slow/hanging in this sandbox.
- Verified contract checks:
  - `python scripts/openapi_contract_snapshot.py --check`
  - `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`
  - `python scripts/frontend_ui_contract_check.py`

## Guardrails preserved

- Read-plane only.
- No validator submission authority.
- No adjudication or ledger mutation authority.
- No promotion or execution authority.
- Lineage readiness is not operator approval and is not live-readiness.
