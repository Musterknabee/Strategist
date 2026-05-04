# Research OS Single-Tenant Handoff Pack

The Research OS handoff pack is a read-plane, digest-linked operator artifact that summarizes whether the latest Research OS evidence can be handed to a single-tenant release reviewer.

It is deliberately **not** deployment approval.

It does not:

- enable live trading
- submit broker orders
- add browser order controls
- grant ledger mutation authority
- certify profitability
- set or change `DEPLOYMENT_APPROVED`

## Inputs

The handoff pack reads existing local artifacts only:

- `research_os_release_readiness/latest/research_os_release_readiness_report.json`
- `research_os_policy_gate/latest/research_os_policy_gate_report.json`
- `research_os_exceptions/latest/research_os_exception_record.json`
- `research_os_remediation/latest/research_os_remediation_plan.json`
- `research_os_exports/latest/research_os_export_manifest.json`
- `research_os_evidence_catalog/latest/research_os_evidence_catalog.json`
- `research_os_drift/latest/research_os_drift_report.json`
- `research_os_operator_runs/latest/research_os_operator_run_manifest.json`
- `research_os_briefings/latest/research_os_briefing_pack.json`
- `research_os_closure/latest/research_os_closure_manifest.json`
- `research_os_attestation/latest/operator_attestation.json`

## Build

```bash
strategy-validator-research-os-handoff build \
  --artifact-root artifacts \
  --handoff-id daily-handoff \
  --overwrite \
  --json
```

Demo:

```bash
python scripts/run_research_os_handoff_demo.py \
  --artifact-root artifacts \
  --handoff-id handoff-demo \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_handoff/
  packs/{handoff_id}/research_os_handoff_pack.json
  latest/research_os_handoff_pack.json
  latest/latest_ref.json
```

## Status vocabulary

- `READY`: handoff-ready with no warnings.
- `RESTRICTED`: handoff-ready for constrained release review only.
- `NOT_READY`: missing or unresolved evidence remains.
- `BLOCKED`: safety or policy evidence blocks handoff.
- `EMPTY`: no meaningful evidence was found.

## Cockpit

Read-plane route:

```text
GET /ui/research-os/handoff/latest
```

Frontend page:

```text
/research-handoff
```

The page shows handoff status, checklist items, source refs, constraints, followups, required operator commands, and digest fields.

## Safety semantics

A `RESTRICTED` handoff is not a bypass. It records constraints and remaining followups so a reviewer can see exactly what evidence is still restricted or degraded.

`BLOCK` policy-gate evidence, false safety flags, or `deployment_approved: true` inside any source artifact block the handoff pack.
