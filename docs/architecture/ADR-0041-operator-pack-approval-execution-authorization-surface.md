# ADR-0041: Operator Pack Approval Execution Authorization Surface

## Status
Accepted

## Context
The control plane already models approval-needed and approval-disposition state for operator packs. It also models downstream dispatch permission. But downstream consumers still lack one reusable surface that answers the practical question:

- is execution authority granted?
- must execution be held pending sign-off?
- is execution authority rejected?

Without a dedicated surface, pack renderers and CLI consumers would need to reinterpret approval disposition plus dispatch permission on their own.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_execution_authorization` as the shared control-plane surface above:

- `operator_pack_approval_disposition`
- `operator_pack_dispatch_permission`

This surface materializes a typed authorization state:

- `AUTHORIZED`
- `HOLD`
- `REJECTED`

with paired authority semantics:

- `EXECUTION_AUTHORIZED`
- `EXECUTION_HELD_PENDING_SIGNOFF`
- `EXECUTION_REJECTED`

and explicit actions:

- `AUTHORIZE_EXECUTION`
- `HOLD_EXECUTION_AUTHORITY`
- `REJECT_EXECUTION_AUTHORITY`

## Consequences
- briefing, status, and incident packs can render one shared execution-authorization section
- the CLI can query the same authorization surface directly
- downstream action surfaces no longer need to reinterpret approval/sign-off posture manually
- the control plane moves one step closer to explicit operator execution authority rather than read-only approval state
