# ADR-0013: Governance work-queue service

## Status
Accepted

## Context
Governance queue/review/routing/dispatch/claim materialization had already been extracted into `control_plane.workflows`, but runtime consumers still reassembled that sequence inline inside validator surfaces. That kept work-queue interpretation mixed into report assembly rather than exposed as a reusable control-plane service.

## Decision
Introduce `strategy_validator.control_plane.operator_queue_service` as the typed control-plane boundary for governance work-queue state.

The service owns:
- typed request/state objects
- review envelope materialization
- routing envelope materialization
- dispatch envelope materialization
- claim envelope materialization

Validator/report surfaces should consume this service rather than rebuilding the queue/review/claim flow inline.

## Consequences
Positive:
- governance work-queue state now has a reusable service boundary
- briefing, advisory, and fusion surfaces share one control-plane path
- pack assembly can consume stable queue/claim/review state from reports built through the same service

Trade-offs:
- workflow functions still exist as lower-level primitives
- compatibility entrypoints remain for now while more validator surfaces are migrated
