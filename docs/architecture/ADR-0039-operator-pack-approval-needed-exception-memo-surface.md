# ADR-0039: Operator pack approval-needed / exception-memo surface

## Status
Accepted

## Context
The control plane can already classify execution exceptions and override posture, but operator-facing surfaces still lacked a reusable approval-needed state that combines override posture with ownership/handoff context.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_approval_needed` as the shared approval-needed / exception-memo read surface above execution-exception plus handoff.

## Consequences
- briefing, status, and incident pack markdown surfaces can render one shared approval-needed section
- the CLI gains a typed approval-needed query surface
- downstream operator workflows can reason about approval-required versus approval-eligible state without reinterpreting raw override posture
