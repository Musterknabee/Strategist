# Semantic Validator Handoff Lineage

`GET /ui/semantic-validator-handoff/lineage` is a read-plane continuity cockpit for the terminal semantic validator handoff path.

It groups discovered semantic handoff artifacts by experiment and verifies the expected lineage:

1. `semantic_adjudication_release_decision_ledger/v1`
2. `semantic_adjudication_release_handoff_certificate/v1`
3. `semantic_validator_handoff_packet/v1`
4. `semantic_validator_handoff_packet_ingress_certificate/v1`

## What it proves

For each chain, the projection checks:

- the handoff certificate references the expected decision ledger id;
- the handoff certificate carries the decision ledger payload checksum;
- the validator packet references the expected handoff certificate id;
- the validator packet carries the handoff certificate payload checksum;
- the ingress certificate references the expected validator packet id;
- the ingress certificate carries the validator packet payload checksum;
- all present components self-verify and are handoff-allowed;
- the ingress certificate is ready for validator ingress.

The route returns `READY`, `BROKEN`, or `INCOMPLETE` chains with issue codes, link checks, component refs, and a chain digest.

## Guardrails

This is deliberately read-only. It does not create artifacts, submit anything to the validator, mutate the adjudication ledger, promote a strategy, or imply operator approval. A `READY` lineage means the discovered artifact chain is internally continuous enough for operator review; it is not live-readiness or production approval.

## Frontend surface

The terminal cockpit page is available at:

- `/semantic-validator-handoff-lineage`

It supports filtering by chain status, operator-review readiness, broken links, experiment id, and issue text. It also lets the operator copy the chain digest into the terminal inspector context.
