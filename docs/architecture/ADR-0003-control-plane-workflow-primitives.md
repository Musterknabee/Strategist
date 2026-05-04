# ADR-0003: Control-plane workflow primitives leave the validator monolith

## Status
Accepted

## Decision
Governance workflow primitives now have a first-class control-plane home in `strategy_validator.control_plane.workflows`.

This includes the typed review, routing, dispatch, and claim envelopes plus the materialization helpers that produce them.

## Why
The repository had already established `control_plane` as the architectural destination for operator workflow logic, but governance workflow materialization still lived entirely under `strategy_validator.validator.oracle_governance_plane`. That kept operator workflow state coupled to the validator monolith and made further extraction harder.

## Consequences
- Downstream operator artifact assembly can depend on `control_plane.workflows` directly.
- `validator.oracle_governance_plane` remains the compatibility surface for assessment logic during the migration window.
- Future slices should move additional governance routing and claim-processing policy out of the validator module and into the control plane.
