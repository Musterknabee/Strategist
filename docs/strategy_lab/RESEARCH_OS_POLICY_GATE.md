# Research OS Policy Gate

The Research OS Policy Gate converts the evidence spine into an explicit operator-review posture:

```text
closure
→ attestation
→ briefing
→ export
→ operator run
→ evidence catalog
→ evidence drift
→ policy gate
```

It is a **read-plane governance artifact**. It does not run research, call providers, call brokers, mutate the ledger, approve deployment, certify profitability, or enable live trading.

## Decisions

- `PASS` — required evidence is present, safety flags remain intact, and no evidence blockers are present. This is still not deployment approval.
- `WARN` — required evidence is present, but some artifacts are restricted/degraded/warning-bearing. Operator review may continue with caution.
- `BLOCK` — a required artifact is missing/unreadable, a blocker exists, an unsafe flag is false, attestation is rejected/blocked, or a secret marker is detected.
- `EMPTY` — no usable required evidence spine is present.

## Inputs

Required inputs:

```text
research_os_operator_runs/latest/research_os_operator_run_manifest.json
research_os_evidence_catalog/latest/research_os_evidence_catalog.json
research_os_closure/latest/research_os_closure_manifest.json
research_os_attestation/latest/closure_verification_result.json
research_os_attestation/latest/operator_attestation.json
research_os_briefings/latest/research_os_briefing_pack.json
research_os_exports/latest/research_os_export_manifest.json
research_os_drift/latest/research_os_drift_report.json
```

Optional inputs include export verification, provider paper loop, provider snapshots, paper broker status, strategy memory, thesis evaluation, and shadow book artifacts.

## CLI

```bash
strategy-validator-research-os-policy-gate build \
  --artifact-root artifacts \
  --gate-id daily-policy-gate \
  --overwrite \
  --json

strategy-validator-research-os-policy-gate latest \
  --artifact-root artifacts \
  --json
```

Demo helper:

```bash
python scripts/run_research_os_policy_gate_demo.py \
  --artifact-root artifacts \
  --gate-id policy-gate-demo \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_policy_gate/
  gates/{gate_id}/research_os_policy_gate_report.json
  latest/research_os_policy_gate_report.json
  latest/latest_ref.json
```

## Read-plane

```text
GET /ui/research-os/policy-gate/latest
GET /ui/research-os/status
```

The consolidated Research OS status embeds `research_os_policy_gate_latest`.

## Frontend

The cockpit page is:

```text
/research-policy-gate
```

It shows the decision, trust banner, input artifacts, rule results, warnings, blockers, recommended operator actions, and SHA-256 evidence spine.

## Safety boundaries

The policy gate preserves these invariants:

- no live trading
- no broker orders
- no browser order controls
- no profitability claim
- no deployment approval mutation
- no provider/broker network calls
- no ledger writer authority

`PASS` means paper-only evidence is internally consistent for operator review. It does **not** mean production deployment approval.
