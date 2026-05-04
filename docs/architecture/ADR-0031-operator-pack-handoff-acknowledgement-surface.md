# ADR-0031: Operator Pack Handoff / Acknowledgement Surface

## Status
Accepted

## Context
The repository already converged operator-pack read models through registry, query, workbench, navigation, dashboard, timeline, comparison, drift, escalation, and assignment. Assignment established who should own worsening pack families, but ownership still remained advisory-only. There was no reusable operator-state surface for whether the handoff was accepted, still pending acknowledgement, or still unclaimed.

## Decision
Introduce a typed control-plane handoff surface in `strategy_validator/control_plane/operator_pack_handoff.py` that sits above operator-pack assignment plus optional operator workboard context.

The new surface:
- materializes explicit handoff states (`HANDOFF_ACCEPTED`, `HANDOFF_PENDING_ACKNOWLEDGEMENT`, `HANDOFF_UNCLAIMED`)
- materializes explicit acceptance states (`ACCEPTED`, `PENDING`, `UNCLAIMED`)
- carries forward queue, review, priority, owner-lane, backup-lane, and summary context
- uses operator workboard entries when available to infer accepted ownership rather than treating every assignment as implicitly claimed
- is consumed by briefing, status, and incident pack markdown renderers
- is exposed through a new CLI command: `oracle-operator-pack-handoff`

## Consequences
### Positive
- The pack plane now expresses explicit operator-state progression rather than stopping at ownership recommendation.
- Worsening pack families can now be rendered as accepted, pending, or unclaimed work across operator-facing surfaces.
- Future queue/claim persistence can attach to a stable control-plane boundary instead of modifying renderer-specific logic.

### Negative
- Acceptance is still inferred from workboard context rather than persisted through a dedicated acknowledgement ledger.
- This introduces another read model that will eventually need to converge with durable queue claim state if/when operator acknowledgements become append-only events.

## Follow-on
Build a typed operator claim/lease state surface so accepted/pending/unclaimed handoffs can converge toward durable acknowledgement and lease semantics instead of inferred state only.
