# ADR-0045: Operator Pack Terminal Closure / Archive Eligibility Surface

## Status
Accepted

## Context
The operator pack plane already models terminal resolution and claim lifecycle, but it still lacks a reusable closure/archive state above those adjacent signals.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_terminal_closure` as the shared surface that converges terminal resolution plus claim lifecycle into terminal closure posture.

## Consequences
Briefing, status, incident, and CLI surfaces can all consume one reusable closure/archive model instead of inferring close/retain/archive behavior inline.
