# ADR-0081: Chronic Remediation Satisfaction

## Status
Accepted

## Context
Chronic remediation mandates freeze return activation for recurrently unstable work items, but the control plane had no typed surface for demonstrating mandate satisfaction or exit-criteria readiness.

## Decision
Introduce `oracle_operator_chronic_remediation_satisfaction/v1` as the canonical evidence surface over chronic remediation mandates. It must materialize satisfaction state, evidence posture, exit-criteria readiness, and freeze-release eligibility.

## Consequences
Chronic remediation can now advance through an evidence-backed satisfaction step instead of jumping directly from mandate history to release decisions.
