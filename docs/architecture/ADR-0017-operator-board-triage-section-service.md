# ADR-0017: Operator board/triage section service

## Decision

Introduce a shared control-plane board/triage section service so operator queue and workboard presentation does not fragment across briefing, status, and incident surfaces.

## Why

The repo already has a queue snapshot seam and a workboard read plane, but presentation logic was still duplicated across validator report renderers and briefing assembly. That duplication would re-fragment the operator surface.

## Result

- `control_plane.operator_board_sections` owns shared operator workboard report conversion
- the same module owns shared markdown rendering for operator workboard sections
- briefing queue-section assembly now uses a shared builder rather than inline field flattening
- status and incident markdown rendering now consume the same shared operator workboard formatter

## Next

Move operator board/triage rendering fully out of validator report modules and let pack assembly consume one shared formatter/section registry.
