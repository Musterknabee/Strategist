# ADR-0009: Projection Query and Operator Consumption

## Status
Accepted

## Context
The repository now emits projection registry sidecars and a shared `ORACLE_PROJECTION_ARTIFACT_INDEX.json`, but operator-facing assemblies still partially depended on canonical filename assumptions. That made the projection registry useful for write-side provenance but underused on the read side.

## Decision
We will make operator-facing consumers resolve projection products through the shared artifact index first, then fall back to legacy filename discovery only for compatibility.

This slice establishes two concrete moves:

1. `oracle_briefing_pack` resolves the canonical event-derived posture through indexed projection discovery rather than only `ORACLE_DERIVED_VIEW.json` / `ORACLE_ROLLING_REVIEW.json` filename assumptions.
2. `oracle_incident_pack` consumes the same indexed discovery path through the status-pack / derived-view resolution flow.
3. The CLI exposes `oracle-projection-artifact-query` so operators can inspect projection products through the platform registry directly.

## Consequences
Positive:
- Operator surfaces can consume valid projection outputs materialized under custom names or nested directories.
- The platform now reads its own projection registry rather than treating it as write-only metadata.
- Future operator surfaces can standardize on the same discovery/query seam.

Tradeoffs:
- Registry/index integrity becomes even more important because it is now part of read-path behavior.
- Compatibility fallbacks remain temporarily to avoid breaking historical file-based workflows.

## Follow-on
- Move more operator surfaces to registry-first consumption.
- Add richer query filters and a stable API surface over projection discovery.
- Gradually de-emphasize canonical filename fallback paths as migration completes.
