# Next Semantic Validator Handoff Remediation Ledger

## Slice

Implemented `ui_semantic_validator_handoff_remediation/v1`, a read-plane-only remediation cockpit that converts semantic validator handoff lineage findings into deterministic operator repair guidance.

## What was added

- Backend projection: `strategy_validator/application/ui_semantic_validator_handoff_remediation.py`
- API routes:
  - `GET /ui/semantic-validator-handoff/remediation`
  - `GET /ui/semantic-validator-handoff/remediation/latest`
- Public facade and OpenAPI snapshot entries for the new routes.
- Frontend cockpit page: `/semantic-validator-handoff-remediation`
- Frontend hook, API payload types, demo-mode payload, query keys, route refresh, terminal rail, and command-palette wiring.
- Regression tests covering ready/no-action, checksum repair, missing-component reconstruction, and route registration.

## Contract posture

The remediation cockpit is advisory/read-plane only:

- no artifact creation or mutation
- no checksum or ID rewriting
- no validator submission authority
- no adjudication, promotion, or execution authority
- remediation steps are operator guidance, not approval

## Validation performed

- `python -m py_compile strategy_validator/application/ui_semantic_validator_handoff_remediation.py strategy_validator/api/routes/ui_routes_detail_runtime.py strategy_validator/application/ui_public_facade.py`
- Direct projection smoke for corrupt packet/certificate checksum lineage.
- Direct FastAPI `TestClient(create_app())` route smoke for `/ui/semantic-validator-handoff/remediation`.
- `python scripts/openapi_contract_snapshot.py --check`
- `python scripts/ui_facade_contract_snapshot.py --check --no-static-fallback`
- `python scripts/generate_frontend_ui_facade_contract.py`
- `python scripts/frontend_ui_contract_check.py`

## Notes

`pytest` collection in this sandbox remained slow/hung for the new application test module, matching the prior lineage-test timeout behavior. The test file was still added, and the same scenarios were validated directly through Python smoke checks.

## Subphase decomposition slice

Decomposed `ui_semantic_validator_handoff_remediation.py` behind a compatibility facade so the remediation read-plane can keep its public contract while moving implementation details into focused modules:

- `ui_semantic_validator_handoff_remediation_common.py` owns constants, component labels, step-library templates, normalization, digesting, counters, and read-plane authority flags.
- `ui_semantic_validator_handoff_remediation_rows.py` owns issue-to-step mapping, remediation status/severity/priority classification, row synthesis, and filtering.
- `ui_semantic_validator_handoff_remediation_payload.py` owns public payload/latest builders and resolves the lineage source through the legacy facade to preserve monkeypatch compatibility.
- `ui_semantic_validator_handoff_remediation.py` is now a thin compatibility facade that re-exports public builders and legacy private helper imports.
- `tests/application/test_ui_semantic_validator_handoff_remediation_decomposition.py` guards facade thinness, subphase ownership, public export identity, private helper import stability, and source-builder monkeypatch behavior.

Validation:

- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/application/test_ui_semantic_validator_handoff_remediation_decomposition.py`: PASS.
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 pytest -q tests/application/test_ui_semantic_validator_handoff_remediation.py -k 'not route_is_registered'`: PASS.
- Direct FastAPI route smoke for `/ui/semantic-validator-handoff/remediation`: PASS.
- `python -m compileall -q strategy_validator tests`: PASS.
- `python scripts/repository_truth_check.py`: PASS.
- `python scripts/migration_truth_check.py`: PASS.
- `python scripts/source_health.py --high-gravity --json`: PASS.
