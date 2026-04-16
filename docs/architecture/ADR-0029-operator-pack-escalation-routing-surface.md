# ADR-0029: Operator Pack Escalation / Routing Surface

## Status
Accepted

## Context
The repository already exposes operator pack query, workbench, navigation, dashboard, timeline, comparison, and drift surfaces. Drift introduces the first action-oriented signal, but pack renderers and operator CLI still lack a reusable routing/escalation surface that turns worsening pack evolution into explicit operator review targeting.

## Decision
Introduce a typed `operator_pack_escalation` control-plane surface that composes pack drift with optional queue/workboard context. The surface assigns escalation posture, routing lane, routing target, and priority band, and provides a shared markdown rendering path consumed by briefing/status/incident pack renderers and a dedicated CLI query command.

## Consequences
- The platform can route worsening pack evolution into explicit operator review semantics instead of only rendering alerts.
- Queue/workboard context can enrich escalation output without making the pack registry depend on governance runtime objects.
- Later work can connect this surface to operator queue snapshots and automated assignment without reworking pack read models.
