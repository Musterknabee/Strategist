# Next Semantic Validator Handoff Clearance Review Docket Ledger

## Slice completed

Added a read-plane-only semantic validator handoff clearance review docket that converts clearance closeout-board cards into deterministic authorized-review routing observations.

## Backend surface

- New application projection: `strategy_validator/application/ui_semantic_validator_handoff_clearance_review_docket.py`
- New API routes:
  - `GET /ui/semantic-validator-handoff/clearance-review-docket`
  - `GET /ui/semantic-validator-handoff/clearance-review-docket/latest`
- New payload schema: `ui_semantic_validator_handoff_clearance_review_docket/v1`
- Source projection: `ui_semantic_validator_handoff_clearance_closeout_board/v1`
- Added filters for docket status/readiness, source closeout status/readiness, evidence lane, priority/severity/trust, owner, authorized-review readiness, human-review requirement, blocked/waiting state, issue text, experiment text, and limit.

## Frontend surface

- New hook: `useUiSemanticValidatorHandoffClearanceReviewDocket`
- New page: `/semantic-validator-handoff-clearance-review-docket`
- Added query keys, route refresh binding, command-palette entry, terminal shell navigation, UI facade contracts, and generated frontend contract.
- OpenAPI snapshot paths were manually patched by mirroring the adjacent closeout-board route shape.

## Authority posture

This docket is visibility only. It has no authority to write review records, assert review completion, authorize review, close out clearance, decide clearance, approve, sign off, write/verify records, acknowledge resolution steps, execute repairs/actions, write external artifacts, mutate artifacts, submit to validator/adjudication, promote, or execute.

## Validation run

- `python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_clearance_review_docket.py strategy_validator/api/routes/ui_routes_detail_runtime.py strategy_validator/application/ui_public_facade.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/application/test_ui_semantic_validator_handoff_clearance_closeout_board.py tests/application/test_ui_semantic_validator_handoff_clearance_review_docket.py tests/api/test_ui_semantic_validator_handoff_clearance_closeout_board_route.py tests/api/test_ui_semantic_validator_handoff_clearance_review_docket_route.py -q`
- `python scripts/ui_facade_contract_snapshot.py --check`
- `python scripts/frontend_ui_contract_check.py`
- `python scripts/source_health.py`
- Direct projection smoke for `build_ui_semantic_validator_handoff_clearance_review_docket_payload(search_root='artifacts', limit=5)`

## Sandbox caveat

- Full OpenAPI regeneration remains expensive in this sandbox, so the new OpenAPI paths were manually patched from the adjacent read-plane route shape and then cross-checked by the UI facade snapshot check.
