# ADR-0071: Operator Return Monitoring Window

## Status
Accepted

## Context
Return activation restores work to normal flow, but restoration alone does not prove the item remained healthy long enough to be considered normalized.

## Decision
Introduce `oracle_operator_return_monitoring/v1` to materialize a bounded monitoring window, drift-watch posture, reopen trigger, and normalization-readiness state for restored operator work.
