# ADR-0046: Operator pack terminal archive / retention surface

## Context
Terminal closure determines whether a pack can close, remain open, or become archive-ready, but operator surfaces still lacked a reusable retention-governance seam tied to the shared pack registry.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_terminal_archive` as the shared surface that converges terminal closure plus the shared pack registry into terminal archive/retention posture.

## Consequences
- briefing/status/incident packs can render a shared retention-governance section
- CLI can emit typed terminal-archive payloads directly from the pack registry
- downstream archival/retention flows can consume one stable surface instead of reinterpreting closure posture ad hoc
