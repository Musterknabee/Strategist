# ADR-0023: Operator Pack Workbench Read Plane

## Status
Accepted

## Context
The repository already emits and indexes operator packs, and it can query raw matches from the shared operator pack index. That is useful, but still too low-level for operators. A higher-order read model is needed so pack families can be presented as structured, navigable collections rather than raw query hits.

## Decision
Introduce a typed operator pack workbench read plane in `strategy_validator.control_plane.operator_pack_workbench`.

This workbench sits above the shared operator pack query/discovery seam and groups indexed packs into operator-facing columns by pack kind, preserving recency ordering and trust metadata.

A dedicated CLI surface, `oracle-operator-pack-workbench`, will consume this service directly.

## Consequences
- operator packs become structured read-plane objects rather than only index matches
- navigation over pack families becomes reusable for future operator dashboards and pack selectors
- CLI remains a thin facade over the typed workbench service
