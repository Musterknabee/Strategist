# ADR-0067: Operator Reentry Post-Remediation Review Gate

## Status
Accepted

## Context
Attestation determines whether remediation looks complete and whether extra review is required, but operators still need a durable gate that decides whether an item may return to normal flow, must wait for review, or stays blocked.

## Decision
Introduce `oracle_operator_reentry_post_review_gate/v1` as the canonical return-authorization gate over completion attestation. The gate must emit review state, authorization outcome, next queue lane, and reviewer identity.

## Consequences
The reentry flow now has an explicit quality gate between remediation completion and return to normal work. This improves trust, operator clarity, and future policy extensibility.
