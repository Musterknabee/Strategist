# Semantic Validator Handoff Runbook Slice

## Slice

Added a read-only semantic validator handoff runbook cockpit that converts continuity rows into deterministic operator next-action cards.

## Backend

- `strategy_validator/application/ui_semantic_validator_handoff_runbook.py`
  - schema: `ui_semantic_validator_handoff_runbook/v1`
  - consumes `ui_semantic_validator_handoff_continuity/v1`
  - emits sorted runbook cards by priority
  - preserves read-plane authority only
- `strategy_validator/api/routes/ui_routes_detail_runtime.py`
  - `GET /ui/semantic-validator-handoff/runbook`
  - `GET /ui/semantic-validator-handoff/runbook/latest`
- `strategy_validator/application/ui_public_facade.py`
  - advertises both routes in the public UI facade contract

## Frontend

- `ui/strategist-web/hooks/useUiSemanticValidatorHandoffRunbook.ts`
- `ui/strategist-web/app/semantic-validator-handoff-runbook/page.tsx`
- terminal rail, command palette, G-chord, route refresh, generated facade contract, demo payloads, and API payload typings updated.

## Guardrails

The slice does not create or mutate closure attestations, archive manifests, validator packets, adjudications, promotions, or execution objects. It only surfaces guidance derived from read-plane continuity state.

## Validation notes

Validated with:

```bash
python -m compileall -q strategy_validator tests scripts
python scripts/generate_frontend_ui_facade_contract.py
python scripts/frontend_ui_contract_check.py
python scripts/ui_facade_contract_snapshot.py --check
python scripts/source_health.py
```

Direct backend test functions in `tests/application/test_ui_semantic_validator_handoff_runbook.py` were also invoked successfully. Full pytest for this single file timed out in the sandbox, matching prior slice behavior where direct invocation is stable but the runner stalls.
