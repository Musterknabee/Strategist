# ADR-0033: Operator pack claim lifecycle / renewal surface

## Status
Accepted.

## Context
The control plane now exposes assignment, handoff, and claim/lease state for operator packs. Active claims, however, are still effectively static snapshots. Operators need a reusable surface that turns claim and lease state into explicit lifecycle guidance: renew, acquire, release, or allow expiry.

## Decision
Introduce a typed `operator_pack_claim_lifecycle` control-plane surface in `strategy_validator/control_plane/operator_pack_claim_lifecycle.py` that composes operator-pack claim/lease state with optional workboard context and emits:

- lifecycle state
- renewal action
- expiry action
- lifecycle label and key
- recommended actions

The new lifecycle surface is consumed by briefing, status, and incident pack markdown renderers and by a dedicated CLI command.

## Consequences
The operator pack plane now moves beyond static claim state into reusable lifecycle guidance. Future operator lease governance can build on this boundary instead of reinterpreting claim status independently in each renderer or CLI tool.
