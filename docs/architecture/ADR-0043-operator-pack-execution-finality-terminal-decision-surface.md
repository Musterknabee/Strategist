# ADR-0043: Operator Pack Execution Finality / Terminal Decision Surface

## Decision
Introduce a typed control-plane surface that converges forced-execution posture and dispatch outcome into a single terminal execution decision plane.

## Consequences
- pack consumers can render terminal execution decisions from one shared seam
- CLI can query terminal execution state directly
- downstream operator logic no longer has to reconcile force posture and dispatch outcome ad hoc
