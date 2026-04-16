# ADR-0087: Application Layer and Bounded Contracts

## Status
Accepted

## Context
The repository has grown strong constitutional and operator-governance coverage, but several surfaces have become oversized:

- `strategy_validator/cli/rollout_ops.py`
- `strategy_validator/cli/oracle_queue_commands.py`
- `strategy_validator/contracts/oracle.py`
- `strategy_validator/control_plane/__init__.py`

This creates architectural drag because transport wiring, orchestration, and contract evolution are landing in broad files instead of bounded service seams.

## Decision
The repository converges around five explicit planes:

1. decision kernel
2. evidence backbone
3. governance plane
4. research ingress
5. application layer

The `application/` package is now the transport-neutral use-case surface for CLI and API code.
New orchestration should land in `strategy_validator.application`, not directly in CLI command modules.

Contract growth must also become bounded. `strategy_validator.contracts.oracle` remains a compatibility surface during migration, but new operator-pack, briefing, governance, and event-view contracts should land in dedicated contract modules.

## Consequences
- CLI code becomes adapter-thin over application services.
- API code can depend on application services without reaching into validator internals.
- Bounded contract modules can evolve without further expanding `contracts/oracle.py`.
- Projection query consumers gain an application-facing seam.
