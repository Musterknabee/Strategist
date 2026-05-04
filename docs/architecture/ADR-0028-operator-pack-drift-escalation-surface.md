# ADR-0028: Operator pack drift / escalation surface

## Status
Accepted

## Context
The platform can now index, query, group, navigate, dashboard, timeline, and compare operator packs. It still lacked a reusable read model that turns those historical changes into operator-relevant alerts.

## Decision
Introduce a typed `operator_pack_drift` control-plane surface that flags worsening or sustained degraded pack evolution above the shared pack index/query seam, and make briefing/status/incident markdown renderers consume the shared drift section.

## Consequences
- Operators get a reusable alert-oriented pack view instead of reconstructing drift from raw comparison output.
- Future escalation/routing logic can build on one typed drift surface rather than duplicating worsening-pack heuristics.
- Pack rendering keeps converging on shared operator-facing read models rather than embedding pack-history interpretation inline.
