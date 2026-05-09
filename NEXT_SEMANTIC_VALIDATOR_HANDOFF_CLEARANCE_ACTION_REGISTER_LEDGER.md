# Next Semantic Validator Handoff Clearance Action Register Ledger

## Slice completed

Added a read-plane-only semantic validator handoff clearance action register that turns clearance operations-board cards into deterministic operator action rows.

## Backend surface

- New application projection: `strategy_validator/application/ui_semantic_validator_handoff_clearance_action_register.py`
- New API routes:
  - `GET /ui/semantic-validator-handoff/clearance-action-register`
  - `GET /ui/semantic-validator-handoff/clearance-action-register/latest`
- New payload schema: `ui_semantic_validator_handoff_clearance_action_register/v1`
- Source projection: `ui_semantic_validator_handoff_clearance_operations_board/v1`
- Added filters for action state/type, operation state/group, lane, priority/severity/trust, owner, external artifact, human review, blocked, ready-candidate, and text contains.

## Frontend surface

- New hook: `useUiSemanticValidatorHandoffClearanceActionRegister`
- New page: `/semantic-validator-handoff-clearance-action-register`
- Added query keys, route refresh binding, command-palette entry, and terminal shell navigation.
- Regenerated UI facade and frontend route contracts.
- Manually patched the OpenAPI snapshot entry for the new read-plane routes because full OpenAPI generation timed out in this sandbox snapshot.

## Authority posture

This register is visibility only. It has no authority to acknowledge actions, execute actions, acknowledge operations, assert coverage, attest evidence, override checks/evidence, approve clearance, sign off, write external artifacts, mutate artifacts, submit to validator/adjudication, promote, or execute.

## Validation run

- `python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_clearance_action_register.py strategy_validator/api/routes/ui_routes_detail_runtime.py strategy_validator/application/ui_public_facade.py`
- `python -m pytest tests/application/test_ui_semantic_validator_handoff_clearance_action_register.py -q -vv`
- `python -m pytest tests/api/test_ui_semantic_validator_handoff_clearance_action_register_route.py -q -vv`
- `python -m pytest tests/application/test_ui_semantic_validator_handoff_clearance_operations_board.py tests/api/test_ui_semantic_validator_handoff_clearance_operations_board_route.py -q`
- `python scripts/ui_facade_contract_snapshot.py --check`
- `python scripts/frontend_ui_contract_check.py`
- `python scripts/source_health.py`
- Direct projection smoke: `build_ui_semantic_validator_handoff_clearance_action_register_payload(search_root='artifacts', limit=5)`

## Sandbox caveats

- `python scripts/openapi_contract_snapshot.py` timed out in this sandbox before producing output. The new OpenAPI paths were added manually by mirroring the existing clearance operations-board route shape and replacing the operation IDs, summaries, response titles, and query parameter list for the action register route.
- A combined pytest invocation that included both the new and adjacent old tests timed out once in this sandbox, while the same tests passed when run separately.
