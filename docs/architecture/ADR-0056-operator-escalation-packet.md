# ADR-0056: Operator Escalation Packet

## Status
Accepted

## Context
Typed escalation routing now identifies which operator actions must leave the standard flow, but routing alone is still too thin for supervisor review. Escalated work needs a durable packet that captures destination, policy reason, class, and remediation obligations in one review-ready artifact.

## Decision
Introduce `oracle_operator_escalation_packet/v1` as the canonical supervisor-ready escalation artifact. Each escalated packet must materialize:

- the routed destination lane and target
- the governing escalation class and policy reason code
- the remediation obligation
- a review checklist that tells the receiving lane what must be confirmed before release

The packet is integrated into the operator control-plane bundle so escalations are reviewable as first-class control-plane state.

## Consequences
Escalation handling stops being a raw routing side effect and becomes a durable review surface. This improves operator handoff, supervisor review quality, and creates the seam for future escalation SLAs, reassignment policies, and audit checkpoints.
