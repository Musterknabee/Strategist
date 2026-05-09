# Next Semantic Validator Handoff Timeline Ledger

## Slice
Semantic Validator Handoff Timeline Cockpit

## Intent
Add a read-only stage-level timeline surface for semantic-validator handoff chains. The slice flattens continuity rows into deterministic events across decision, signoff, custody, archive, and closure so an operator can see where evidence is recorded, missing, blocked, or awaiting an external artifact.

## Backend
- Added `strategy_validator/application/ui_semantic_validator_handoff_timeline.py`.
- Added schema `ui_semantic_validator_handoff_timeline/v1`.
- Added routes:
  - `GET /ui/semantic-validator-handoff/timeline`
  - `GET /ui/semantic-validator-handoff/timeline/latest`
- Added filtering by experiment, issue text, stage, event state, severity, and ready-event inclusion.

## Frontend
- Added `/semantic-validator-handoff-timeline` page.
- Added `useUiSemanticValidatorHandoffTimeline` hook.
- Added TypeScript payload/event types.
- Wired terminal rail, command palette, G-chord route, route refresh invalidation, and demo-mode payloads.

## Authority posture
This slice is read-plane only. It does not write artifacts, mutate evidence, submit validator packets, adjudicate, promote, or execute anything.

## Validation
- `pytest -q tests/application/test_ui_semantic_validator_handoff_timeline.py`
- `python -m compileall -q strategy_validator/application strategy_validator/api tests/application scripts`
- `python scripts/ui_facade_contract_snapshot.py --check`
- `python scripts/frontend_ui_contract_check.py`
- `timeout 45s python scripts/source_health.py`

## Caveat
The working sandbox reset removed the later non-uploaded authority/health working artifacts. This slice was built from the newest available uploaded archive in `/mnt/data`: `Strategist-semantic-validator-handoff-exceptions-slice.zip`.
