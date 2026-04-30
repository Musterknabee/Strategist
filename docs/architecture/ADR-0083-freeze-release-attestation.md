# ADR-0083: Freeze-Release Attestation

## Status
Accepted

## Context
Freeze-release authorization decides whether chronic remediation may leave the frozen state, but it does not yet record a certification boundary over the evidence posture.

## Decision
Introduce `oracle_operator_freeze_release_attestation/v1` as the evidence-backed attestation surface over freeze-release gate outputs.

## Consequences
Release authorization becomes certifiable rather than only review-approved. This strengthens the control-plane boundary before chronic work may rejoin the return path.
