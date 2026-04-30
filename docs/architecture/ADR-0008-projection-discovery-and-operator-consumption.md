# ADR-0008: Projection discovery and operator-surface consumption

## Status
Accepted

## Context
The repository now emits projection registry sidecars and a shared `ORACLE_PROJECTION_ARTIFACT_INDEX.json` for canonical event-log views, checkpoints, and briefing-pack artifacts. That created a write-time governance seam, but operator-facing read paths still depended on direct filename discovery such as `ORACLE_ROLLING_REVIEW.json` or `ORACLE_HORIZON_VIEW.json`.

That pattern keeps output families tightly coupled to canonical filenames and prevents operator surfaces from consuming indexed projection products that were materialized under alternate names or nested pack directories.

## Decision
Introduce a projection discovery/query layer in `strategy_validator.projections.discovery` and make operator-facing diagnostics consume it before falling back to direct filename search.

The first consumer is `build_oracle_status_pack`, which now resolves the current derived oracle posture by querying the shared projection artifact index for canonical event projections in priority order:

1. `oracle_rolling_review`
2. `oracle_horizon_view`
3. `oracle_derived_view`

This preserves backward compatibility through filename fallback while moving operator workflow quality toward registry-backed discovery.

## Consequences
- Projection outputs become discoverable platform objects rather than isolated files.
- Operator surfaces can consume valid indexed projections even when artifact names differ from legacy defaults.
- The artifact index now participates in both write-time provenance and read-time workflow assembly.
- Remaining operator surfaces should migrate to the same discovery/query path so pack assembly stops depending on brittle file naming conventions.
