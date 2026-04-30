# ADR-0030: Operator Pack Assignment / Ownership Surface

## Context

The control plane now materializes operator pack drift and escalation. That gives the platform a reusable signal for worsening pack evolution, but it still stops at routing advice.

The next convergence seam is ownership: pack escalations should materialize a typed recommendation for who should take the handoff, which backup lane should cover the work, and how that handoff should be expressed across operator surfaces.

## Decision

Introduce a shared `operator_pack_assignment` control-plane surface that sits above pack escalation and produces:

- ownership posture
- primary owner lane
- backup owner lane
- owner label / handoff target
- recommended actions

Wire real consumers through it:

- `oracle-operator-pack-assignment` CLI surface
- briefing-pack markdown
- status-pack markdown
- incident-pack markdown

## Consequences

This moves the pack read plane from:

- alerting about worsening evolution
- routing escalating pack families

into:

- assigning accountable owner lanes
- recommending handoff targets
- making ownership presentation reusable across operator surfaces

This is a direct convergence step toward a true operator orchestration plane.
