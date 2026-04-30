# ADR-0074: Operator Return Reopen Loop

## Status
Accepted

## Context
A drift breach is useful only if it can restart governed remediation.

## Decision
Introduce `oracle_operator_return_reopen_loop/v1` as the canonical return-to-remediation loop over breached or unstable restored work.

## Consequences
The control plane gains an explicit closed-loop path from restoration failure back into reentry work.
