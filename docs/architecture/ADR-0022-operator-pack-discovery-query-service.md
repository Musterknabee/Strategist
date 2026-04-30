# ADR-0022: Operator Pack Discovery and Query Service

## Status
Accepted

## Context
Operator pack materialization now emits a shared manifest and index family via `ORACLE_OPERATOR_PACK_MANIFEST.json` and `ORACLE_OPERATOR_PACK_INDEX.json`. That write-side convergence is necessary but not sufficient. Without a typed read/query seam, operator packs remain discoverable only by ad hoc filename/path archaeology.

## Decision
Introduce a typed operator-pack discovery and query service over the shared pack index. The service must:

- resolve indexed pack manifests and pack roots from one or more `ORACLE_OPERATOR_PACK_INDEX.json` files
- support filtering by pack kind, trust status, summary-line substring, and output-artifact labels
- expose a typed operator-facing payload for CLI and future operator-read-plane consumers
- provide a `discover_latest_operator_pack_match(...)` helper for deterministic latest-pack selection

A new CLI surface, `oracle-operator-pack-query`, is registered against this service so the platform can inspect its own pack registry directly.

## Consequences
Positive:
- operator packs become first-class readable platform objects, not just written bundle directories
- future operator surfaces can resolve latest or filtered pack families from index metadata rather than hard-coded paths
- the pack registry now mirrors the projection registry pattern with a converged read plane

Trade-offs:
- pack-index schema stability becomes more important because it now has direct consumers
- path resolution rules must remain explicit across repo-root-relative and index-relative entries

## Follow-on
The next convergence step should promote this query seam into a higher-level operator pack workbench/discovery surface so status, incident, and briefing navigation can resolve indexed pack families from one reusable read model.
