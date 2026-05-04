# ADR-0057: Operator Escalation SLA and Aging Policy

## Status
Accepted

## Context
Escalation packets are now durable supervisor-review artifacts, but they are timeless. Without explicit due-state, breach posture, and urgency semantics, operators cannot distinguish a newly routed escalation from a stale or breached escalation.

## Decision
Introduce `oracle_operator_escalation_sla/v1` as the canonical aging and urgency layer for escalation packets. The SLA surface must derive:

- due-by timestamps from escalation class and governance priority band
- aging posture (`WITHIN_SLA`, `DUE_SOON`, `BREACHED`)
- breach posture (`BREACH_NONE`, `BREACH_IMMINENT`, `BREACH_ACTIVE`)
- review urgency (`ROUTINE`, `URGENT`, `IMMEDIATE`)

The operator control-plane bundle must carry the escalation SLA artifact family as a first-class bundled section.

## Consequences
Escalated work becomes time-governed rather than timeless. This improves supervisor prioritization, enables future escalation dashboards and reminders, and creates a clean seam for stronger policy enforcement later.
