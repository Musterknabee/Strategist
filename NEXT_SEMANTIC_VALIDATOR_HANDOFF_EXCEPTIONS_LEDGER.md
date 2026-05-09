# Semantic Validator Handoff Exceptions Slice

## Scope

Adds a read-only Semantic Validator Handoff Exceptions cockpit that derives unresolved exception rows from the semantic-validator handoff runbook. The slice is intentionally projection-only and does not create artifacts, mutate evidence, submit validator packets, adjudicate, promote, or execute.

## Backend

- `strategy_validator/application/ui_semantic_validator_handoff_exceptions.py`
- `GET /ui/semantic-validator-handoff/exceptions`
- `GET /ui/semantic-validator-handoff/exceptions/latest`

The payload schema is `ui_semantic_validator_handoff_exceptions/v1` and includes:

- exception rows keyed by runbook card
- exception state / kind counts
- priority, severity, and escalation-lane counts
- external artifact requirement counts
- degraded indicators for blocked or external-artifact-required rows
- explicit authority fields all set to read-plane/no-authority

## Frontend

- `/semantic-validator-handoff-exceptions`
- `useUiSemanticValidatorHandoffExceptions`
- API payload types
- terminal rail entry
- command palette / G-chord route
- route-refresh invalidation
- demo-mode payloads

## Validation performed

- Targeted Python syntax compilation for the new backend, route, and test files.
- Direct invocation of the new backend unit test functions.
- `python scripts/generate_frontend_ui_facade_contract.py`
- `python scripts/frontend_ui_contract_check.py`
- `python scripts/ui_facade_contract_snapshot.py --check`

## Notes

`python scripts/source_health.py` failed with a sandbox client error in this environment after targeted validations had already passed. `npm run typecheck` was not run because the uploaded archive does not include `node_modules`.
