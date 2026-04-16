# ADR-0087: Monitored Rejoin Activation

## Status
Accepted

## Context
Chronic exit certification can now bridge back into the return path through monitored rejoin policy, but policy alone does not represent the moment when chronic work is actually reactivated into live operator flow.

## Decision
Introduce `oracle_operator_monitored_rejoin_activation/v1` as the typed activation boundary for chronic rejoin work. The activation must distinguish monitored, standard, and blocked rejoin states and preserve the lane that the work is being restored into.

## Consequences
Chronic work no longer stops at a bridge or policy label. It becomes an explicit activation artifact that can be audited, handed off, and fed into the next monitoring seam.
