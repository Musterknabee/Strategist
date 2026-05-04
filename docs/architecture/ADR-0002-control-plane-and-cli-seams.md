# ADR-0002: Establish control-plane posture seams and CLI command registration seams

## Status
Accepted

## Context
The repository has accumulated operator-control posture logic under `strategy_validator.validator`
and command registration logic inline inside `strategy_validator.cli.rollout_ops`. Both patterns
increase architecture drag and make future decomposition riskier.

## Decision
- Control-plane posture logic should live under `strategy_validator.control_plane`.
- `strategy_validator.validator.oracle_*_posture` and trust-plane modules remain compatibility
  shims during migration.
- Canonical Oracle Event Log commands should register through a dedicated CLI registry module
  rather than growing directly inside the rollout monolith.

## Consequences
- Future posture and operator workflow logic gains a clean destination package.
- CLI decomposition can proceed command-family by command-family without a flag day.
- Legacy import stability is preserved while architecture convergence advances.
