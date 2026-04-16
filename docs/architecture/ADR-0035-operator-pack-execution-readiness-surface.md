# ADR-0035: Operator Pack Execution Readiness Surface

## Status
Accepted

## Context
The control plane now converges pack evolution into drift, escalation, assignment, handoff, claim lifecycle, and lease governance surfaces. What is still missing is a reusable operator-facing decision seam that answers the operational question: should the operator execute now, block execution, or await acknowledgement?

Without that seam, pack governance still ends as a rendered recommendation rather than an explicit readiness/read-plane object that downstream operator surfaces can reuse.

## Decision
Introduce a typed `operator_pack_execution_readiness` control-plane surface that composes:
- lease governance decisions
- handoff acknowledgement state
- optional workboard context

The surface emits explicit operator execution posture:
- `EXECUTE_NOW`
- `BLOCK_EXECUTION`
- `AWAIT_ACKNOWLEDGEMENT`

and paired readiness/action state:
- `READY_TO_EXECUTE`
- `EXECUTION_BLOCKED`
- `AWAITING_ACKNOWLEDGEMENT`

with corresponding execution actions:
- `EXECUTE_DECISION`
- `BLOCK_AND_RELEASE`
- `REQUEST_ACKNOWLEDGEMENT`

## Consequences
- pack governance no longer stops at retain/release/acquire decisions
- briefing/status/incident surfaces can render shared execution posture
- CLI/operator flows can consume a reusable readiness object instead of recomputing this logic inline
- the pack plane advances from governance rendering toward explicit operator execution posture
