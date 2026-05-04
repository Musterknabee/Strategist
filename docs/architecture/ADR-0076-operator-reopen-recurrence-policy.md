# ADR-0076: Operator Reopen Recurrence Policy

## Status
Accepted

## Context
Once reopen lineage exists, the control plane needs a typed policy layer that decides when a reopened work item remains a first-reopen remediation case and when it becomes a recurrent or chronic instability requiring supervisor escalation.

## Decision
Introduce `oracle_operator_reopen_recurrence_policy/v1` as the canonical recurrence-policy artifact over reopen lineage. The policy classifies non-recurrent, first-reopen, repeat-reopen, and chronic-reopen states and emits escalation posture plus recommended queue lane.

## Consequences
Repeated post-return failures now become policy-governed rather than anecdotal. This creates a clear seam for chronic-instability dashboards, recurrence SLOs, and escalation-after-N-reopens governance.
