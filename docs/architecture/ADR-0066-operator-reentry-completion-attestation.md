# ADR-0066: Operator Reentry Completion Attestation

## Status
Accepted

## Context
The operator reentry flow now reaches a typed completion artifact, but completion alone does not certify that a remediation cycle is safe to return to normal flow. The control plane needs an explicit attestation surface that states whether completion is return-ready, review-gated, deferred, or blocked.

## Decision
Introduce `oracle_operator_reentry_completion_attestation/v1` as the canonical certification layer over remediation completion. The attestation must record attestor identity, attestation state, review requirement, review scope, and whether return to normal flow is safe.

## Consequences
Completion becomes a governed certification step rather than a cosmetic terminal label. This creates a clean seam for post-remediation review gates, safe return authorization, and future attestor accountability.
