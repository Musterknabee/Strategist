# ADR-0077: Operator Chronic Instability Packet

## Status
Accepted

## Context
Reopen recurrence policy classifies structurally unstable work, but classification alone is not a durable escalation artifact.

## Decision
Introduce `oracle_operator_chronic_instability_packet/v1` as the durable escalation packet for recurrent and chronic reopened remediation work. The packet captures recurrence class, tribunal lane, remediation obligation, and review checklist.

## Consequences
Recurrence becomes a first-class escalation artifact rather than an advisory label, enabling downstream tribunal/supervisor routing and explicit remediation obligations.
