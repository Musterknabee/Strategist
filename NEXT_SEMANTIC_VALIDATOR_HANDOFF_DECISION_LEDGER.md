# Next Semantic Validator Handoff Decision Dossier Ledger

## Slice

Semantic Validator Handoff Decision Dossier Cockpit.

## Purpose

Adds a deterministic read-plane layer above the semantic validator handoff review gate. The new layer prepares operator decision dossiers that summarize whether a handoff chain is safe to draft for manual signoff, which preconditions pass or block, which decision options remain available, and which authority surfaces remain forbidden.

## Backend

- Added `strategy_validator/application/ui_semantic_validator_handoff_decision.py`.
- Added read routes:
  - `GET /ui/semantic-validator-handoff/decision`
  - `GET /ui/semantic-validator-handoff/decision/latest`
- Added facade entries for both routes.
- Added `tests/application/test_ui_semantic_validator_handoff_decision.py`.

## Frontend

- Added `/semantic-validator-handoff-decision` cockpit page.
- Added `useUiSemanticValidatorHandoffDecision` hook.
- Added decision payload TypeScript contracts.
- Added query keys, command-palette entry, terminal rail entry, route-refresh invalidation, and demo-mode payloads.
- Regenerated frontend UI facade contract JSON/TS.

## Guardrails

- Read-plane only.
- Does not write signoff records.
- Does not create, edit, restore, or regenerate artifacts.
- Does not submit validator packets.
- Does not promote releases.
- Does not grant execution authority.
- Human reviewer/signoff fields remain explicit external placeholders.

## Validation

- `python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_decision.py strategy_validator/api/routes/ui_routes_detail_runtime.py tests/application/test_ui_semantic_validator_handoff_decision.py`
- Direct semantic decision validation for:
  - ready clean chain
  - checksum repair chain
  - incomplete lineage chain
  - FastAPI route registration through `TestClient(create_app())`
- `python scripts/openapi_contract_snapshot.py --check`
- `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`
- `python scripts/frontend_ui_contract_check.py`
- `python scripts/source_health.py`

## Notes

`pytest` collection remains unreliable in this sandbox for these semantic handoff tests, consistent with earlier slices. The new assertions were validated directly with temporary artifacts and the FastAPI route smoke.
