# ADR-0024: Operator pack selector/navigation service

## Status
Accepted

## Context
The repository already has pack manifests, a shared pack index, a typed pack query seam, and a workbench read model. What was still missing was a reusable selector/navigation layer for "latest relevant pack" resolution. That logic would otherwise start leaking into briefing/incident/status surfaces as ad hoc filtering.

## Decision
Introduce a typed operator pack navigation service in `strategy_validator.control_plane.operator_pack_navigation`. The service sits above the workbench read plane, selects latest relevant packs by kind/order, and provides a reusable markdown navigation surface.

Consume that service in real runtime pack renderers so briefing/status/incident surfaces can render related indexed packs without duplicating selection logic.

## Consequences
- latest relevant pack resolution is now a reusable control-plane service
- pack surfaces can expose navigation without reimplementing query/filter logic
- future operator consoles can build on the selector rather than raw workbench columns
