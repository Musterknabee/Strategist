# Next Slice Ledger — Semantic Validator Handoff Evidence Gaps

Added a read-only `ui_semantic_validator_handoff_evidence_gaps/v1` cockpit that derives evidence-gap rows from semantic-validator handoff timeline events.

## Added

- Backend projection: `strategy_validator/application/ui_semantic_validator_handoff_evidence_gaps.py`
- Tests: `tests/application/test_ui_semantic_validator_handoff_evidence_gaps.py`
- API routes:
  - `GET /ui/semantic-validator-handoff/evidence-gaps`
  - `GET /ui/semantic-validator-handoff/evidence-gaps/latest`
- Frontend route: `/semantic-validator-handoff-evidence-gaps`
- Frontend hook, API types, query keys, terminal rail, command palette, route refresh, demo-mode payloads
- UI facade/generated frontend contract and OpenAPI snapshot entries

## Authority posture

Read-plane only: no mutation, no external artifact write, no artifact mutation, no validator submission, no adjudication, no promotion, no execution.

## Gap categories

- `MISSING_STAGE_EVIDENCE_GAP`
- `BLOCKED_STAGE_EVIDENCE_GAP`
- `EXTERNAL_ARTIFACT_GAP`
- `ATTENTION_STAGE_EVIDENCE_GAP`
- `CURRENT_STAGE_OPEN_GAP`
- `RESOLVED_AUDIT_REFERENCE` when explicitly requested
