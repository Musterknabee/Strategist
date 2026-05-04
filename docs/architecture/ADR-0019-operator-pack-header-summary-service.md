# ADR-0019: Operator pack header / summary service

## Status
Accepted

## Context
Status, incident, and briefing pack renderers had already converged on shared section composition, but they still owned their top-level header and summary blocks independently. That left a duplicated presentation seam in the validator runtime surface.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_headers` as the shared operator-facing header / summary plane for pack markdown renderers.

This service owns:
- pack title selection
- top-level metadata line assembly
- top-level summary block assembly
- shared markdown header rendering

Validator renderers remain compatibility entrypoints, but consume the control-plane header builder instead of owning the top-level banner logic inline.

## Consequences
Positive:
- pack renderers now share a single summary/header seam
- top-level pack metadata can evolve without copy-pasting changes across renderers
- convergence now includes operator presentation framing, not only section composition

Tradeoffs:
- briefing-pack header logic remains large because the report surface itself is still large
- HTML rendering is not yet on the shared seam and remains a later extraction target
