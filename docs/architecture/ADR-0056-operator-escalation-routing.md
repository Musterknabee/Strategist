# ADR-0056: Operator Escalation Routing

## Status
Accepted

## Context
Decision execution can now determine whether a requested operator transition is accepted, blocked, or escalated. That is still insufficient for operator control-plane use because an escalated decision without a typed destination lane and remediation obligation remains opaque.

## Decision
Introduce `oracle_operator_escalation_routing/v1` as the canonical escalation-routing surface for governed operator executions. The routing artifact must identify whether escalation is required, the destination lane, the escalation class, and the remediation obligation.

## Consequences
Escalated operator work becomes routable and reviewable. This gives downstream automation and human operators an explicit control-plane seam for escalation handling instead of treating escalation as a generic terminal status.
