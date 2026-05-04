# ADR-0006: Event-view projection registry for horizon and rolling review

## Status
Accepted

## Context
The canonical Oracle Event Log has already become the preferred convergence path for horizon-view and rolling-review surfaces. Until now, these surfaces emitted reports and markdown directly, but they did not emit an explicit projection-registry sidecar that recorded canonical source lineage and output-artifact lineage in a shared projection format.

That left horizon and rolling-review partially converged in data sourcing but not yet converged in projection governance.

## Decision
Introduce a shared event-view projection seam under `strategy_validator/projections/` and require canonical event-log view surfaces to emit projection-registry sidecars whenever they materialize output artifacts.

This extraction adds:

- `strategy_validator/projections/query_build.py`
- `strategy_validator/projections/oracle_event_views.py`

and wires:

- `oracle-horizon-view`
- `oracle-rolling-review`

through the shared event-view projection registry builder.

## Consequences
Positive:

- horizon-view and rolling-review now behave like governed projection products rather than stand-alone outputs
- canonical event-log lineage is explicit in emitted sidecars
- shared projection-builder logic now exists for later migration of additional event-log-driven surfaces

Negative:

- registry sidecars are currently emitted only when a materialized output path is requested
- checkpoint flows still need to be migrated onto the same explicit projection query/build layer

## Follow-on work
- migrate horizon checkpoint and rolling-review checkpoint onto the same projection-registry pattern
- introduce a richer projection query/build contract for multi-source canonical projections
- migrate additional output families away from inline provenance assembly
