# ADR-0034: Operator Pack Lease Governance / Release Decision Surface

## Status
Accepted

## Context
The control plane already materializes claim lifecycle guidance and escalation posture for operator packs. What it still lacks is a reusable governance decision surface that converges lifecycle guidance into retain, renew, release, or expiry decisions.

## Decision
Introduce `strategy_validator.control_plane.operator_pack_lease_governance` as the shared surface above claim lifecycle and escalation. This surface owns typed lease-governance decisions, release posture, routing context, and shared markdown rendering.

## Consequences
- briefing, status, and incident pack markdown can consume one shared governance section
- CLI surfaces can emit typed governance payloads directly
- claim lifecycle advice now converges into reusable governance decisions instead of remaining only advisory
