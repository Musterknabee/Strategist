# Semantic Validator Handoff Review Slice

## Purpose

Adds a read-only operator review gate above the semantic validator handoff remediation queue. The slice answers a different question from the base handoff index, lineage verifier, and remediation queue:

- handoff index: which validator handoff artifacts exist?
- lineage: do ledger → certificate → packet → ingress certificate links bind together?
- remediation: what must be repaired before review?
- review gate: is this chain safe for operator review, and which checklist items pass or block?

## Backend

Added `strategy_validator/application/ui_semantic_validator_handoff_review.py` with schema `ui_semantic_validator_handoff_review/v1`.

The projection derives from `ui_semantic_validator_handoff_remediation/v1` and emits:

- deterministic `review_id`
- `review_status`
- `trust_banner`
- immutable authority booleans
- review checklist rows
- component evidence map
- blocker codes
- summary counts and degraded signals

It remains a read-plane only projection:

- no artifact creation or mutation
- no validator submission
- no adjudication authority
- no promotion authority
- no execution authority

## API

Added routes:

- `GET /ui/semantic-validator-handoff/review`
- `GET /ui/semantic-validator-handoff/review/latest`

Filters:

- `experiment_id_contains`
- `issue_contains`
- `review_status`
- `trust_banner`
- `operator_review_allowed`
- `limit`

## Frontend

Added cockpit page:

- `/semantic-validator-handoff-review`

Added frontend support:

- hook: `useUiSemanticValidatorHandoffReview`
- API types
- query keys
- route refresh invalidation
- command palette entry
- terminal rail entry
- demo-mode payload
- regenerated frontend facade contracts

## Tests / validation

Added `tests/application/test_ui_semantic_validator_handoff_review.py` covering:

- clean ready chain becomes `READY_FOR_OPERATOR_REVIEW`
- checksum break becomes blocked/untrusted review
- incomplete lineage requires reconstruction before review
- API route registration and payload shape

Validated with direct test-function smoke runs and contract checks.

## Guardrails

The review gate intentionally does not equate operator review readiness with approval, validator submission, promotion, live readiness, or execution authority.
