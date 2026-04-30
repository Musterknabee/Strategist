# ADR-0014: Operator queue snapshot surface

## Status
Accepted

## Context
The control plane already owned the governance assessment and work-queue envelope materialization paths, but operator-facing runtime surfaces still consumed raw governance claim fields directly when building reports.

That left the operator workflow state implicit:
- queue/review/dispatch/claim envelopes existed
- but there was no typed operator work-item surface above them
- pack/report builders still reached into raw claim fields instead of consuming explicit operator queue state

## Decision
Introduce a typed operator queue snapshot surface in `strategy_validator.control_plane.operator_queue_snapshot`.

The snapshot layer:
- materializes a typed `OracleOperatorWorkItem`
- materializes a typed `OracleOperatorQueueSnapshot`
- sits above `operator_queue_service`
- becomes the reusable control-plane read surface for pack/report consumers that need operator queue state

Initial consumers:
- `validator/oracle_briefing.py`
- `validator/oracle_signal_fusion.py`

## Consequences
Positive:
- operator workflow state is now explicit rather than buried in raw governance claim fields
- pack/report builders consume a typed control-plane surface
- future queue inspection / queue query CLI work has a natural source model

Trade-offs:
- validator still emits legacy flat report fields for compatibility
- the snapshot layer currently wraps one primary work item rather than a multi-item queue inventory

## Follow-on
Use this snapshot surface to build:
- operator queue inspection commands
- queue snapshot projections
- pack sections that render explicit work-item state instead of flattened claim fields
