# ADR-0037: Operator Pack Dispatch Outcome / Block-Reason Surface

## Status
Accepted

## Context
Dispatch permission converges execution-readiness plus claim/lease state into permit/hold/block posture, but downstream operator surfaces still need a reusable explanation of what execution outcome that posture implies and why blocked paths are blocked.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_dispatch_outcome` as the shared surface above dispatch permission plus lease-governance context. This surface owns typed dispatch outcomes, execution outcome semantics, block reasons, and shared markdown rendering.

## Consequences
- Briefing, status, and incident packs consume one shared dispatch-outcome section.
- CLI can emit typed dispatch-outcome payloads directly from the shared pack registry.
- Later execution and audit surfaces can consume stable block reasons instead of reverse-engineering them from dispatch posture.
