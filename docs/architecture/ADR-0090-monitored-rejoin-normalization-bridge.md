# ADR-0090: Monitored Rejoin Normalization Bridge

## Status
Accepted

## Context
Once chronic watch produces a typed outcome, the control plane still needs an explicit bridge back into the existing normalization path or reopen path. Without that bridge, chronic monitored rejoins remain isolated from the broader return lifecycle.

## Decision
Introduce `oracle_operator_monitored_rejoin_normalization_bridge/v1` as the typed bridge from chronic watch outcomes into normalization, continued watch, or reopen routing.

## Consequences
The chronic branch now converges back into the main operator lifecycle instead of ending in a local monitoring result. This preserves architectural coherence and gives later slices a clean place to add post-bridge monitoring and reopen policy.
