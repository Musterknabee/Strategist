# ADR-0080: Chronic Remediation Mandate Ledger

## Status
Accepted

## Context
Tribunal dispositions are not enough on their own; the system needs replayable mandate history that freezes return activation until recurrence-specific remediation is satisfied.

## Decision
Introduce `oracle_operator_chronic_remediation_mandate_ledger/v1` as the durable mandate-history surface over tribunal dispositions.

## Consequences
Chronic instability moves from review-only posture into a durable remediation governance layer.
