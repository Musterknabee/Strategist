# ADR-0063: Operator Reentry Acknowledgement Timeout and Reminder Policy

## Status
Accepted

## Context
Reentry assignment and acknowledgement surfaces make remediation ownership explicit, but pending acknowledgements can still sit indefinitely with no time semantics. That leaves requeued remediation work visible but not governable.

## Decision
Introduce `oracle_operator_reentry_acknowledgement_timeout/v1` as the canonical timeout and reminder surface for pending remediation acknowledgements.

The surface must:
- derive timeout windows from remediation class and handoff posture
- calculate due-by timestamps and timeout status for pending acknowledgements
- produce reminder state and escalation triggers when acknowledgements are due soon or breached
- materialize as a durable artifact family and be included in the operator control-plane bundle

## Consequences
Pending acknowledgement work becomes time-governed rather than passive. This creates the next seam for reminder delivery, reassignment, and supervisor escalation on stuck remediation ownership.
