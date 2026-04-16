# ADR-0064: Operator Reentry Rejection and Reassignment Loop

## Status
Accepted

## Context
The operator control plane now models reentry assignment, acknowledgement posture, and acknowledgement timeout. However, timed-out or declined ownership still terminates at policy posture. There is no durable reassignment artifact that routes remediation work to a backup owner or supervisor lane.

## Decision
Introduce `oracle_operator_reentry_reassignment/v1` as the typed reassignment artifact for reentry work. The reassignment layer must:

- derive reassignment requirements from acknowledgement timeout posture
- route breached assignee ownership to a backup owner, handoff target, or supervisor lane
- preserve the prior assignee label and explicit reason code
- materialize JSON and markdown outputs suitable for operator review and downstream automation

## Consequences
The reentry loop becomes closed under ownership failure. Timed-out remediation work can now move to a backup owner or escalation lane as a first-class control-plane artifact rather than remaining a passive breach state.
