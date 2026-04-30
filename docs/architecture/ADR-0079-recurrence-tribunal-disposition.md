# ADR-0079: Recurrence Tribunal Disposition

## Status
Accepted

## Context
Recurrence tribunal routing identifies structurally unstable work but does not yet record the durable decision that freezes return activation and mandates recurrence-specific remediation.

## Decision
Introduce `oracle_operator_recurrence_tribunal_disposition/v1` as the durable decision record over recurrence tribunal lane outputs.

## Consequences
The control plane can now distinguish routing from decision and replay chronic-instability review outcomes.
