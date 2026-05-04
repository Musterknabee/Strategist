# ADR-0072: Operator Restoration Audit Trail

## Status
Accepted

## Context
The system needs a durable audit surface that distinguishes monitored returns from normalized returns and restoration attempts that must reopen or remain blocked.

## Decision
Introduce `oracle_operator_restoration_audit/v1` to materialize restoration audit state, normalization outcome, and reopen-after-restoration semantics over return monitoring artifacts.
