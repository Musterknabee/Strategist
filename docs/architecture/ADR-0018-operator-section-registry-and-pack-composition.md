# ADR-0018: Operator section registry and pack composition

## Status
Accepted

## Decision
Introduce a shared operator section registry / pack composition service in `strategy_validator.control_plane.operator_section_registry`.

## Rationale
Status, incident, and briefing packs had already converged on shared queue, workboard, and operator-section builders, but each pack surface still owned its own section-ordering and section-selection logic. That was the next fragmentation loop.

The new registry/composition seam centralizes:
- status-pack section ordering
- incident-pack section ordering
- briefing-pack section ordering
- inclusion of shared operator workboard sections
- terminal next-action section composition

## Consequences
- pack renderers now consume a shared operator-facing section plane
- section ordering changes can be made once and applied across pack surfaces
- validator renderers remain compatibility facades instead of the authoritative section composition layer
