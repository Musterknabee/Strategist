# ADR-0084: Chronic Exit Certification

## Status
Accepted

## Context
After freeze-release attestation, the control plane still lacks a final certification artifact that says whether a chronic issue is safe to rejoin the return-authorization path.

## Decision
Introduce `oracle_operator_chronic_exit_certification/v1` as the typed chronic-exit certification surface over freeze-release attestations.

## Consequences
Chronic remediation now ends in a replayable certification decision with explicit rejoin posture and routing semantics.
