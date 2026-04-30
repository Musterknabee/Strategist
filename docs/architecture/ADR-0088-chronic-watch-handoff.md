# ADR-0088: Chronic Watch Handoff

## Status
Accepted

## Context
Once chronic work is reactivated under monitored rejoin policy, the system still needs a typed handoff into the live return-monitoring loop so the chronic path does not remain isolated from the broader restoration lifecycle.

## Decision
Introduce `oracle_operator_chronic_watch_handoff/v1` as the durable handoff artifact between monitored rejoin activation and the existing return monitoring / reopen seams.

## Consequences
Chronic rejoin becomes a first-class monitored pathway with explicit monitoring authority, watch window, reopen target, and auditability.
