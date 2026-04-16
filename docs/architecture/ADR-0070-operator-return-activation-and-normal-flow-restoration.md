# ADR-0070: Operator Return Activation and Normal-Flow Restoration

## Status
Accepted

## Context
The control plane can now produce post-remediation review dispositions and a durable return authorization ledger, but it still stops at authorization history. There is no typed artifact that expresses whether an authorized remediation item was actually restored into normal operator flow, held for rework, or kept under supervisor control.

## Decision
Introduce `oracle_operator_return_activation/v1` as the activation surface over return authorization history. The artifact must explicitly record: activation state, restored queue lane, whether normal flow was restored, and whether post-return monitoring is required.

## Consequences
The control plane now distinguishes between permission to return and actual restoration to the normal operator queue. This creates the next seam for post-return monitoring, restoration audits, and guarded normalization workflows.
