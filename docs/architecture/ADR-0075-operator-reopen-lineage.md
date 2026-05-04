# ADR-0075: Operator Reopen Lineage

## Status
Accepted

## Context
Post-return reopen loops now identify when restored work falls back into governed remediation. Without lineage, every reopen looks isolated and the control plane cannot distinguish one-off drift from repeated instability.

## Decision
Introduce `oracle_operator_reopen_lineage/v1` as the canonical artifact for reopened remediation cycle history. The lineage surface records prior reopen count, current reopen count, cycle index, and whether the current reopen advanced remediation lineage.

## Consequences
The control plane can reason about reopened work across cycles instead of treating each reopen as a fresh event. This is the prerequisite for recurrence-aware escalation and chronic-instability policy.
