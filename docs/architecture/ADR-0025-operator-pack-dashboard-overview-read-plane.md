# ADR-0025: Operator Pack Dashboard Overview Read Plane

## Status
Accepted

## Context
The repository already had pack registry, query, workbench, and navigation seams, but operator-facing surfaces still consumed them piecemeal. That left briefing, status, and incident packs to decide independently how to present pack families as an operational board.

## Decision
Introduce a typed `operator_pack_dashboard` read plane in `strategy_validator.control_plane` that composes:
- pack workbench grouping
- latest relevant pack navigation
- top-level overview metrics

Real operator-facing pack renderers should consume this dashboard seam instead of directly composing navigation-only output.

## Consequences
- Pack families become a coherent operational board rather than a set of separate query tools.
- Status, incident, and briefing pack markdown can consume one dashboard presentation seam.
- Future UI and API surfaces can depend on the dashboard read model instead of rebuilding overview logic again.
