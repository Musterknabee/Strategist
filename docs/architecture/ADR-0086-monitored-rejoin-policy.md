# ADR-0086: Monitored Rejoin Policy

## Status
Accepted

## Context
A bridged chronic exit still needs a typed rejoin policy so the system can distinguish blocked, standard, and heightened-monitoring rejoin postures before it flows back into the existing return path.

## Decision
Introduce `oracle_operator_monitored_rejoin_policy/v1` as the typed rejoin-policy surface over chronic-exit return bridges.

## Consequences
Chronic exit no longer ends at certification. It now feeds a durable rejoin-policy surface that can be audited and later connected to return authorization and monitoring execution.
