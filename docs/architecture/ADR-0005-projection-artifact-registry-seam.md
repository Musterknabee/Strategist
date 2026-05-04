# ADR-0005: Projection Artifact Registry Seam

## Status
Accepted

## Context
The repo had multiple higher-order operator outputs such as briefing packs, horizon views, and digest/report families, but those outputs still behaved mostly like independent artifact families with inline provenance logic. That shape makes long-run convergence harder because every new output family tends to grow its own source-discovery and lineage story.

## Decision
Introduce an explicit projection/artifact-registry seam under `strategy_validator/projections/`.

The first production use is the briefing-pack family:
- `strategy_validator/projections/artifact_registry.py`
- `strategy_validator/projections/briefing_pack.py`

The `oracle-briefing-pack` CLI now emits a projection registry sidecar that records:
- projection label/family/version
- canonical source artifact descriptors
- output artifact descriptors
- projection digest fingerprint

## Consequences
This does not yet make all outputs pure projections, but it establishes the governing seam for that migration.

Near-term follow-ons:
1. move horizon-view / rolling-review outputs onto the same registry pattern
2. add typed projection builders for pack/digest families
3. centralize artifact registry querying rather than re-deriving source discovery in each operator surface
