# ADR-0062: Operator Reentry Acceptance and Ownership Acknowledgement

## Status
Accepted

## Context
Reentry assignment now materializes ownership, assignee routing, and handoff posture for remediation work returning from escalation closure. However, the control plane still lacks an explicit acknowledgement artifact that states whether ownership has been accepted automatically, requires assignee acknowledgement, or remains pending handoff.

## Decision
Introduce `oracle_operator_reentry_acceptance/v1` as the canonical acknowledgement surface for reentry assignments. The acceptance layer must:

- derive acknowledgement state from assignment posture rather than silently assuming acceptance
- distinguish auto-acknowledged ownership from assignee-pending and handoff-pending work
- publish a durable JSON and markdown artifact family that can be bundled into the operator control plane

## Consequences
The operator reentry loop now has an explicit handshake surface between assignment and execution. This improves accountability, makes stuck ownership visible, and creates a clean seam for future reminder, timeout, and rejection policy.
