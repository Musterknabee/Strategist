# ADR-0089: Chronic Watch Outcome

## Status
Accepted

## Context
The chronic rejoin path already activates monitored rejoins and hands them into a watch lane, but the system lacked a typed outcome surface describing whether the watch stayed active, stabilized, breached, or remained blocked.

## Decision
Introduce `oracle_operator_chronic_watch_outcome/v1` as the durable outcome artifact over chronic watch handoffs. The artifact must classify each watched item into stable, active, breached, or blocked states and explicitly capture normalization eligibility versus reopen obligation.

## Consequences
Chronic watch is no longer a terminal monitoring artifact. It now produces a replayable result that downstream control-plane logic can bridge into normalization or reopen routing.
