# ADR-0048: Operator Pack Claim Operability Surface

## Status
Accepted

## Context
The control plane already exposes claim lifecycle, lease governance, and execution readiness, but operators still have to infer whether a pack family is actually operable from those adjacent surfaces.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_claim_operability` as the typed surface that normalizes execution-readiness plus claim lifecycle into canonical `CLAIM_OPERABLE`, `CLAIM_CONSTRAINED`, and `CLAIM_INOPERABLE` posture.

## Consequences
- briefing/status/incident pack markdown can consume one explicit claim-operability section
- CLI gains `oracle-operator-pack-claim-operability`
- downstream automation can key on one posture contract instead of re-deriving operability from execution and lease state
