# ADR-0021: Operator pack manifest and index service

## Status
Accepted.

## Context
Briefing, status, and incident packs had converged on shared assembly, headers, sections, and HTML rendering, but they still behaved like standalone outputs once materialized. The platform could write packs, but it did not register them as one discoverable family with typed metadata.

## Decision
Introduce a shared operator-pack manifest and index service under `strategy_validator.projections.operator_pack_registry`.

Each materialized pack now emits:
- `ORACLE_OPERATOR_PACK_MANIFEST.json` inside the pack root
- `ORACLE_OPERATOR_PACK_INDEX.json` at the shared parent/index root

The manifest records:
- pack kind
- report schema version
- report provenance digest
- trust status
- summary line
- pack root
- output artifact descriptors
- copied artifact descriptors
- pack digest

The shared index records one discoverable family for:
- `status_pack`
- `incident_pack`
- `briefing_pack`

## Consequences
Positive:
- packs are now registered as first-class platform outputs
- pack materialization has a reusable lookup surface
- later operator discovery/query flows can resolve packs through an index instead of file-name assumptions

Trade-offs:
- pack materialization now owns one more write side effect
- compatibility wrappers remain in validator until pack discovery migrates further upward
