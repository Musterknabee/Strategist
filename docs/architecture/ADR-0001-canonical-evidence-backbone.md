# ADR-0001: Canonical evidence backbone

## Status
Accepted

## Decision
The system will converge around a canonical event and evidence backbone. New decision, briefing, workflow, and governance surfaces must either:

- emit canonical events, or
- be projections derived from canonical events and typed evidence artifacts.

## Consequences
- Legacy lane append chains are frozen for feature growth.
- Operator workflow logic gains an explicit `control_plane` home.
- Replayability and provenance become the default standard for new surfaces.
