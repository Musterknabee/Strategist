# ADR-0060: Operator Reentry Remediation Queue State

## Status
Accepted

## Context
Escalation closure can now resolve, hold open, or requeue work. Without a typed reentry surface, requeued items disappear into an implied next step instead of becoming governed operator work with explicit remediation obligations.

## Decision
Introduce `oracle_operator_reentry_queue_state/v1` as the canonical remediation reentry surface for escalation closures that return to operator flow.

The reentry state must:
- include only requeued escalation closures
- rejoin each item with the originating action contract
- carry remediation reason, remediation class, and required operator action
- materialize a durable JSON and markdown artifact family
- appear in the operator control-plane bundle as a first-class section

## Consequences
The escalation loop now closes back into operator work instead of ending at an abstract requeue status. This creates a clean seam for remediation dashboards, assignment, and eventual operator SLA / reminder policies.
