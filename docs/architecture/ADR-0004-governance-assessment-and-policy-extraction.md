# ADR-0004: Governance assessment and policy extraction into control_plane

## Status
Accepted

## Context
The repository had already extracted trust posture primitives and workflow-envelope materialization into `strategy_validator.control_plane`, but the governance assessment and routing policy core still lived under `strategy_validator.validator.oracle_governance_plane`. That left the validator namespace acting as both decision kernel and operator workflow/policy surface.

## Decision
Move the following policy surfaces into `strategy_validator.control_plane`:

- operator escalation posture
- control-plane assessment composition
- governance assessment and routing/queue policy core

Keep `strategy_validator.validator.oracle_*` modules as compatibility shims during the convergence period.

## Consequences
New control-plane development should land in:

- `strategy_validator.control_plane.escalation`
- `strategy_validator.control_plane.control_plane`
- `strategy_validator.control_plane.governance_plane`
- `strategy_validator.control_plane.workflows`

The validator namespace remains stable for existing imports, but it is no longer the implementation home for governance policy assembly.

This makes the emerging architecture clearer:

- validator: judgment and validation compatibility surfaces
- control_plane: operator workflow, posture, routing, and governance policy assembly
- evidence / ledger: canonical lineage and event backbone
