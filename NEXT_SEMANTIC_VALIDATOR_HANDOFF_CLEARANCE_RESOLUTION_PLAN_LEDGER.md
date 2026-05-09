# Next Semantic Validator Handoff Clearance Resolution Plan Ledger

## Slice completed

Added a read-plane-only semantic validator handoff clearance resolution plan that turns clearance action-register rows into deterministic operator resolution steps.

## Backend surface

- New application projection: `strategy_validator/application/ui_semantic_validator_handoff_clearance_resolution_plan.py`
- New API routes:
  - `GET /ui/semantic-validator-handoff/clearance-resolution-plan`
  - `GET /ui/semantic-validator-handoff/clearance-resolution-plan/latest`
- New payload schema: `ui_semantic_validator_handoff_clearance_resolution_plan/v1`
- Source projection: `ui_semantic_validator_handoff_clearance_action_register/v1`
- Added filters for evidence lane, phase, step state, action state/type, priority/severity/trust, owner, blocker/external-artifact/human-review/ready state, issue text, experiment text, and limit.

## Frontend surface

- New hook: `useUiSemanticValidatorHandoffClearanceResolutionPlan`
- New page: `/semantic-validator-handoff-clearance-resolution-plan`
- Added query keys, route refresh binding, command-palette entry, terminal shell navigation, UI facade contracts, and generated frontend contract.
- OpenAPI snapshot paths were manually patched because full OpenAPI check timed out in this sandbox.

## Authority posture

This plan is visibility only. It has no authority to materialize plans, acknowledge steps/actions/operations, execute repairs/actions, assert coverage/evidence/checks, override checks/evidence, approve clearance, sign off, write external artifacts, submit to validator/adjudication, promote, or execute.

## Validation run

- `python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_clearance_resolution_plan.py strategy_validator/api/routes/ui_routes_detail_runtime.py strategy_validator/application/ui_public_facade.py`
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/application/test_ui_semantic_validator_handoff_clearance_resolution_plan.py tests/api/test_ui_semantic_validator_handoff_clearance_resolution_plan_route.py -q`
- `python scripts/ui_facade_contract_snapshot.py --check`
- `python scripts/frontend_ui_contract_check.py`
- `python scripts/source_health.py`

## Sandbox caveat

- `python scripts/openapi_contract_snapshot.py --check` timed out in this sandbox. The OpenAPI snapshot was patched by mirroring the existing read-plane route shape and adding the new route parameters.
