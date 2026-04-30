# ADR-0036: Operator Pack Dispatch Permission Surface

## Status
Accepted

## Context
The operator pack control plane had converged through lease governance and execution readiness, but downstream action gating still stopped at rendered posture. That left CLI and pack consumers with readiness semantics instead of a reusable permission boundary.

## Decision
Introduce a typed `operator_pack_dispatch_permission` surface above execution readiness and claim/lease state.

This surface classifies operator pack families into reusable dispatch states:
- `DISPATCH_PERMITTED`
- `DISPATCH_BLOCKED`
- `DISPATCH_AWAITING_ACKNOWLEDGEMENT`

It also carries a downstream action gate:
- `ALLOW_DOWNSTREAM_ACTION`
- `DENY_DOWNSTREAM_ACTION`
- `HOLD_DOWNSTREAM_ACTION`

## Consequences
- downstream action gating is now reusable rather than implied by readiness text
- briefing/status/incident packs can render the same dispatch-permission section
- CLI gains a first-class operator dispatch query surface
- future dispatch or automation adapters can consume a typed permission boundary instead of pack-specific rendering
