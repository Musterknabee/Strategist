# ADR-0007: Projection artifact index and checkpoint registry convergence

## Status
Accepted

## Context
Projection registry sidecars now exist for briefing packs, horizon views, and rolling reviews, but checkpoint-producing event-log surfaces still emitted their artifacts without the same governed registry layer. Projection sidecars also existed as standalone files without a typed discovery index, which limited operator workflow reuse and projection introspection.

## Decision
We will:

1. emit projection registry sidecars for canonical event-log checkpoint-producing surfaces;
2. treat those sidecars as projection products over canonical event-log truth;
3. maintain a typed `oracle_projection_artifact_index/v1` index alongside emitted projection registries so the control plane can discover and query available projection artifacts without scanning arbitrary files.

## Consequences
- `oracle-event-checkpoint`, `oracle-horizon-checkpoint`, and `oracle-rolling-review-checkpoint` now emit governed projection registries.
- projection families update a shared `ORACLE_PROJECTION_ARTIFACT_INDEX.json` in their artifact directory.
- future operator discovery/query surfaces can resolve available projection products through a typed index rather than bespoke directory walking.
- the event-log projection path remains the canonical source of truth for checkpoint surfaces.
