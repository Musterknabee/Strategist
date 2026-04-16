# ADR-0068: Operator Post-Remediation Review Disposition

## Status
Accepted

## Context
The post-remediation review gate currently tells us whether return is authorized, pending, blocked, or still in reentry. That state is useful, but it is not yet a durable reviewer decision artifact.

## Decision
Introduce `oracle_operator_post_review_disposition/v1` as the typed reviewer decision surface over post-remediation review gates. The disposition artifact records approval, denial, rework-required, or escalation outcomes with reviewer identity and reason codes.

## Consequences
The control plane gains a durable review decision seam. This makes return decisions replayable, auditable, and suitable for downstream authorization history.
