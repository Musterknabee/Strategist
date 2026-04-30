# ADR-0059: Operator Escalation Closure Loop

## Status
Accepted

## Context
A supervisor disposition is not enough unless the control plane can express what happens next. The system needs a canonical closure artifact that marks escalations as resolved, re-queued for remediation, or still open.

## Decision
Introduce `oracle_operator_escalation_closure/v1` as the canonical closure-loop artifact. Each closure item must encode:

- the upstream supervisor review decision
- closure status
- next queue lane
- next state
- closure reason code
- whether remediation is still required

## Consequences
Escalations become a closed-loop control-plane workflow instead of a one-way routing side effect.
