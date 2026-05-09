# Next Semantic Validator Handoff Archive Ledger

## Slice

Semantic Validator Handoff Custody + Archive Verification Cockpit.

## What changed

- Added `ui_semantic_validator_handoff_custody/v1` read-plane projection.
- Added `ui_semantic_validator_handoff_archive/v1` read-plane projection.
- Added API routes for `/ui/semantic-validator-handoff/custody`, `/custody/latest`, `/archive`, and `/archive/latest`.
- Added terminal cockpit pages for custody-seal verification and archive-manifest verification.
- Added hooks, query keys, route refresh, terminal navigation, command palette entries, demo payloads, public facade routes, generated frontend contracts, and OpenAPI snapshot entries.
- Added regression coverage for custody and archive read-plane states.

## Authority boundaries

These surfaces are read-plane only. They do not write custody seals, write archive manifests, mutate artifacts, submit validator packets, adjudicate, promote, or execute.

## Validation

- Python compile checks passed for the new backend projections, routes, and tests.
- `scripts/source_health.py` passed.
- `scripts/openapi_contract_snapshot.py --check` passed.
- `scripts/ui_facade_contract_snapshot.py --check --no-static-fallback` passed.
- `scripts/frontend_ui_contract_check.py` passed.
- Direct projection validation passed for ready, recorded, digest-mismatch, and blocked states across custody and archive gates.

## Sandbox caveats

- Full pytest/TestClient execution hangs in this sandbox for this repo family, consistent with previous semantic handoff slices.
- Frontend typecheck cannot complete cleanly without installed frontend dependencies/types; dependency-resolution noise dominates the output.
