# Next Semantic Validator Handoff Signoff Ledger

## Slice

Semantic Validator Handoff Signoff Receipt Cockpit.

## Purpose

Extend the semantic validator handoff cockpit chain from decision dossiers into a read-only verification surface for externally-created human operator signoff receipts.

```text
handoff artifacts
→ lineage continuity
→ remediation queue
→ operator review gate
→ decision dossier
→ signoff receipt verification
```

## Added

- `strategy_validator/application/ui_semantic_validator_handoff_signoff.py`
- `GET /ui/semantic-validator-handoff/signoff`
- `GET /ui/semantic-validator-handoff/signoff/latest`
- `/semantic-validator-handoff-signoff` frontend cockpit page
- `useUiSemanticValidatorHandoffSignoff` hook
- frontend API types, query keys, command-palette, rail, refresh, demo payload, and facade contract wiring
- `tests/application/test_ui_semantic_validator_handoff_signoff.py`

## Operator semantics

The projection verifies whether a signoff JSON receipt exists and matches a deterministic decision packet digest.

Supported statuses:

- `OPERATOR_SIGNOFF_RECORDED`
- `AWAITING_OPERATOR_SIGNOFF`
- `SIGNOFF_INVALID`
- `SIGNOFF_DIGEST_MISMATCH`
- `BLOCKED_DECISION_NOT_SIGNABLE`

## Non-authority assertions

This slice is read-plane-only. It never:

- writes operator signoff receipts
- mutates artifacts
- submits packets to a validator
- promotes releases
- grants execution authority

All authority counters for validator submission, promotion, and execution remain zero.

## Validation

Validated with:

```bash
python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_signoff.py strategy_validator/api/routes/ui_routes_detail_runtime.py tests/application/test_ui_semantic_validator_handoff_signoff.py
python scripts/openapi_contract_snapshot.py --check
python scripts/ui_facade_contract_snapshot.py --check
python scripts/frontend_ui_contract_check.py
python scripts/source_health.py
```

Additional direct backend validation covered:

- awaiting external signoff
- matching external receipt recorded
- decision packet digest mismatch
- blocked non-ready decision

## Caveats

Full FastAPI `TestClient` and full pytest collection can hang in this sandbox for this repo family; the slice was validated with direct projection checks and static/contract gates.
