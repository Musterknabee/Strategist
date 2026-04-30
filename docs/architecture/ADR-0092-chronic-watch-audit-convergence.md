# ADR-0092: Chronic Watch Audit Convergence

## Status
Accepted

## Context
The chronic branch could classify a normalized monitored rejoin, but it did not converge that state back into the standard restoration evidence loop.

## Decision
Introduce `oracle_operator_chronic_watch_audit_convergence/v1` as the typed convergence surface that maps chronic-origin normalization activations into standard return-monitoring and restoration-audit semantics, including normalization confirmation, continued monitoring, or reopen.
