# ADR-0040: Operator pack approval disposition / sign-off state surface

## Status
Accepted

## Context
The operator pack governance plane already materializes approval-needed posture, but downstream consumers still have to infer whether a pack family is effectively approved, awaiting sign-off, or denied based on approval-needed plus claim/lease context.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_approval_disposition` as the typed sign-off state surface above approval-needed and claim/lease state.

## Consequences
- approval-needed posture converges into reusable operator sign-off state
- briefing/status/incident packs can render approval disposition through one shared control-plane seam
- CLI/operator surfaces can consume approved / pending-signoff / denied state without rebuilding inference logic
