# ADR-0015: Operator queue query surface

## Status
Accepted

## Context
The control plane now owns governance workflow primitives, work-queue materialization, and operator queue snapshots. But operators still lacked a direct read surface for explicit work-item state, and pack rendering still flattened queue semantics into scattered claim fields.

## Decision
Introduce a typed operator queue query boundary in `strategy_validator.control_plane.operator_queue_query` and expose it through a dedicated CLI command, `oracle-operator-queue-query`.

Also promote operator queue state into the briefing pack as an explicit `operator_queue` section derived from the queue snapshot service, rather than relying only on flattened governance claim fields.

## Consequences
- The control plane now exposes an operator-facing queue inspection surface.
- CLI/operator workflows can inspect queue state without scraping pack internals.
- Briefing packs render explicit queue/work-item facts from a typed control-plane seam.
- This creates the next clean path toward a reusable operator workboard / queue dashboard surface.
