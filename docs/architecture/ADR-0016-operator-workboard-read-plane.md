# ADR-0016: Operator workboard read plane

## Decision
Introduce a typed operator workboard surface above queue query/snapshot services and make status-pack and incident-pack consume it as structured operator state.

## Why
Status and incident surfaces should not each flatten queue semantics ad hoc. A shared workboard view gives the control plane one reusable operator-facing read model for triage, due windows, urgency, and recommended actions.

## Consequences
- `control_plane.operator_workboard` becomes the typed workboard read plane
- status-pack and incident-pack embed `operator_workboard`
- CLI gains an explicit `oracle-operator-workboard-query` command
