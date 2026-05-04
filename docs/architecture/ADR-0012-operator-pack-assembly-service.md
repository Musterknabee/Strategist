# ADR-0012: Operator pack assembly service

## Status
Accepted

## Context
The repository had already extracted a projection read plane and a pack materialization plane, but the pack build path still lived inside validator modules. `build_oracle_status_pack`, `build_oracle_incident_pack`, and `build_oracle_briefing_pack` remained the places where source resolution, assembly entry, and pack orchestration were owned.

That kept the architecture in an in-between state:
- pack writing had a service boundary
- projection discovery had a service boundary
- but pack assembly still looked like validator-owned runtime logic

## Decision
Introduce a typed operator pack assembly service in `strategy_validator/projections/operator_pack_assembly.py`.

The service now defines explicit assembly request types for:
- status packs
- incident packs
- briefing packs

Validator modules remain stable compatibility facades, but they delegate public pack assembly entrypoints to the projection-side service.

## Consequences
Positive:
- establishes an explicit pack assembly plane above discovery and materialization
- keeps validator as a compatibility namespace instead of the long-term home for operator bundle orchestration
- gives CLI and future API surfaces a reusable assembly boundary

Trade-offs:
- implementation internals are still in transition; this ADR extracts the boundary first and preserves compatibility while deeper logic continues moving behind it

## Follow-on work
- move more assembly internals behind projection/control-plane services instead of validator-private helpers
- let CLI and API surfaces call the assembly plane directly where appropriate
- converge pack policy inputs into typed assembly policies instead of widening function signatures further
