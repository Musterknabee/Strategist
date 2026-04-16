# ADR-0010: Projection service read-plane boundary

## Status
Accepted

## Context
The repo had already established write-side projection registry and artifact index seams, but projection discovery and operator query behavior were still split across inline CLI code and validator runtime consumers. That left selection policy, query rendering, and operator-facing consumption partially mixed with command wiring and report assembly.

## Decision
Introduce a typed projection service boundary in `strategy_validator/projections/service.py` that owns:

- projection artifact query construction
- operator query execution
- canonical event projection selection
- stable payload rendering for operator-facing query surfaces

Use that service from both runtime consumers and CLI command entrypoints.

## Consequences
- validator runtime paths now consume a reusable read-plane boundary instead of directly performing projection discovery
- operator query CLI behavior is no longer implemented inline in `rollout_ops.py`
- canonical event projection selection becomes an explicit platform capability rather than a repeated helper pattern
- future API/read-plane work can build on the same typed service without re-embedding selection logic in commands
