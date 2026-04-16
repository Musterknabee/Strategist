# ADR-0065: Operator Reentry Completion and Evidence Closure

## Status
Accepted

## Context
The operator control plane can now route remediation back into operator flow, assign ownership, track acknowledgement timeout, and reassign or escalate breached work. What it still lacks is a typed completion surface that closes the remediation cycle with evidence posture and explicit return-to-normal semantics.

## Decision
Introduce `oracle_operator_reentry_completion/v1` as the canonical completion artifact for reentry remediation cycles. The surface must:

- evaluate accepted and reassigned remediation cycles into typed completion outcomes
- emit an explicit evidence posture and evidence reason code for every completion record
- distinguish returned-to-normal operation from reassigned, escalated, and still-open remediation cycles
- integrate into the operator control-plane bundle as the terminal remediation-cycle closure surface

## Consequences
The reentry path now has a typed end-state rather than stopping at reassignment. This gives the operator plane a durable closure artifact that can later feed normal-state restoration, evidence dashboards, remediation quality audits, and policy-backed post-remediation review.
