# ADR-0058: Operator Supervisor Review Disposition

## Status
Accepted

## Context
Escalation routing, packets, and SLA aging make escalations visible, but the control plane still lacks an explicit supervisor disposition artifact. Without a typed review result, escalations remain operationally ambiguous and cannot cleanly close, return to operator remediation, or remain open under review.

## Decision
Introduce `oracle_operator_supervisor_review/v1` as the canonical supervisor disposition artifact. Each review item must encode:

- the escalated packet under review
- supervisor disposition
- disposition reason code
- review status
- closure recommendation
- actor identity and review timestamp

## Consequences
Supervisor review becomes durable, inspectable, and replayable. This creates a strict seam between escalation visibility and escalation resolution.
