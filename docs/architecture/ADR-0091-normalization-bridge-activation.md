# ADR-0091: Normalization Bridge Activation

## Status
Accepted

## Context
Chronic watch outcomes can now bridge back toward normalization, but the repository lacked a first-class activation seam that reconnects those bridge decisions into the standard return-monitoring and restoration-audit loop.

## Decision
Introduce `oracle_operator_normalization_bridge_activation/v1` as the typed activation surface for chronic-origin normalization bridges. It must preserve chronic origin, declare the standard return-monitoring and restoration-audit targets, and carry a durable activation timestamp for the converged monitoring window.
