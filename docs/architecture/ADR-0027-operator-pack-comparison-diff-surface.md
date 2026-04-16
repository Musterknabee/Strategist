# ADR-0027: Operator pack comparison / diff surface

## Status
Accepted.

## Context
The platform can now index, query, group, navigate, dashboard, and timeline operator packs. It still lacks a reusable comparison surface for inspecting how recent pack generations changed between runs.

## Decision
Introduce a typed control-plane comparison surface over the shared operator pack index that compares the latest and previous generations per pack kind and exposes tracked change fields for operator-facing rendering and CLI query.

## Consequences
- Pack evolution is inspectable as an explicit read model instead of being inferred from timeline entries alone.
- Briefing, status, and incident pack renderers can consume one shared comparison section.
- Future consoles can build richer diffs on top of the comparison surface without reimplementing latest/previous selection logic.
