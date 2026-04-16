# ADR-0082: Freeze Release Gate

## Status
Accepted

## Context
Once chronic remediation is satisfied, the control plane still needs an explicit governance step that decides whether the return freeze can be released.

## Decision
Introduce `oracle_operator_freeze_release_gate/v1` as the canonical release-decision layer over chronic remediation satisfaction. It must produce durable release authorization or hold posture and route work back into the appropriate return-authorization lane.

## Consequences
Return-freeze decisions become replayable governance artifacts rather than implicit assumptions hidden in downstream routing.
