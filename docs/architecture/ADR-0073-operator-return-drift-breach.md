# ADR-0073: Operator Return Drift Breach

## Status
Accepted

## Context
The control plane can restore operator work and audit its monitoring outcome, but it still lacks a typed surface for post-return drift or unstable restoration.

## Decision
Introduce `oracle_operator_return_drift_breach/v1` as the canonical surface for post-return breach posture. It classifies stable, watched, reopened, and actively breached returns and marks whether remediation must reopen.

## Consequences
The system can now fail restored work honestly and route it back into governed remediation when stability does not hold.
