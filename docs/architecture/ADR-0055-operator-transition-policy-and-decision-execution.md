# ADR-0055: Operator Transition Policy and Decision Execution

## Status
Accepted

## Context
The operator control plane emits workboard contracts, journals, outcome ledgers, and feedback state, but it still lacks the policy seam that decides which transitions are allowed now, which must escalate, and which remain record-only. Without that seam, downstream outcomes can overstate actual operability.

## Decision
Introduce two first-class surfaces:

- `oracle_operator_transition_policy/v1` as the typed policy layer over workboard action contracts
- `oracle_operator_decision_execution/v1` as the policy-governed execution report that converts requested transitions into effective transitions

The action outcome ledger must derive from decision execution rather than from unconstrained requested state.

## Consequences
The control plane now expresses governed action semantics rather than raw intent. This improves auditability, policy enforcement, and future replay or automation work because every outcome is grounded in an explicit transition policy decision.
