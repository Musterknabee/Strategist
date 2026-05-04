# ADR-0061: Operator Reentry Assignment and Remediation Ownership

## Status
Accepted

## Context
The control plane now materializes reentry remediation work after escalation closure, but requeued work still lacks explicit ownership, acceptance posture, and handoff accountability. That leaves remediation items visible but not operationally accountable.

## Decision
Introduce `oracle_operator_reentry_assignment/v1` as the typed ownership surface for remediation reentry work. The surface must:

- assign each reentry item to an owner lane and assignee label
- distinguish acceptance-required assignments from auto-accepted assignments
- emit handoff requirements and explicit handoff targets
- remain derived from reentry queue state rather than mutating work items in place

## Consequences
Reentry work becomes accountable operator work rather than passive queue state. This creates a clean seam for future acceptance events, reminder policy, load balancing, and operator capacity tracking.
