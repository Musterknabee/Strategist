# ADR-0069: Operator Return Authorization Ledger

## Status
Accepted

## Context
A review disposition is still not enough on its own. The control plane needs an append-safe history of whether remediation work was actually authorized back into normal flow, denied, reworked, or escalated.

## Decision
Introduce `oracle_operator_return_authorization_ledger/v1` as the durable authorization history over post-review dispositions. The ledger records authorization state, history state, next queue lane, and reviewer identity.

## Consequences
Return-to-normal decisions become explicit control-plane history rather than an implied consequence of gate state. This improves traceability and enables future replay, audit, and reporting.
