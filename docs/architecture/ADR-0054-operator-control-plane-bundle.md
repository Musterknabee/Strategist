# ADR-0054: Operator Control Plane Bundle

## Status
Accepted

## Context
The operator control plane has reached the point where queue query, workboard, action contract, decision journal, outcome ledger, and feedback state all exist as distinct typed surfaces. Operators still lack a single durable artifact family that captures the full control-plane state for review, replay, and downstream automation.

## Decision
Introduce `oracle_operator_control_plane_bundle/v1` as the canonical control-plane materialization. The bundle emits a top-level JSON/markdown summary plus nested durable artifacts for the decision journal, action outcome ledger, and feedback state.

## Consequences
The control plane becomes a publishable artifact family rather than a collection of disconnected commands. This improves handoff, replay, and future policy enforcement while keeping the implementation thin and typed.
