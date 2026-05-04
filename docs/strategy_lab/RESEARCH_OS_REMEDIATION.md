# Research OS Remediation Plan

The Research OS remediation plan converts the latest policy-gate, governed-exception, evidence-catalog, and evidence-drift signals into a digest-linked operator action queue.

It is **read-plane guidance only**. It does not approve deployment, live trading, broker orders, browser order controls, or profitability claims.

## Artifact

```text
artifacts/research_os_remediation/
  plans/{plan_id}/research_os_remediation_plan.json
  latest/research_os_remediation_plan.json
  latest/latest_ref.json
```

## CLI

```bash
strategy-validator-research-os-remediation build \
  --artifact-root artifacts \
  --plan-id daily-remediation \
  --overwrite \
  --json

strategy-validator-research-os-remediation latest --artifact-root artifacts --json
```

Demo wrapper:

```bash
python scripts/run_research_os_remediation_demo.py \
  --artifact-root artifacts \
  --plan-id research-os-remediation-demo \
  --overwrite \
  --json
```

## Inputs

The builder reads existing local artifacts only:

- `research_os_policy_gate/latest/research_os_policy_gate_report.json`
- `research_os_exceptions/latest/research_os_exception_record.json`
- `research_os_evidence_catalog/latest/research_os_evidence_catalog.json`
- `research_os_drift/latest/research_os_drift_report.json`

Missing inputs become remediation items; they do not trigger network calls.

## Semantics

- `READY`: no open remediation items were produced.
- `RESTRICTED`: open or waived items exist, but no plan-level blocker exists.
- `BLOCKED`: blocking evidence or missing critical governance evidence exists.
- `EMPTY`: no useful source evidence exists.

Item priorities:

- `P0`: safety/security/tamper/blocker remediation.
- `P1`: required governance evidence missing.
- `P2`: restricted provider/broker/drift/governance evidence.
- `P3`: low-priority optional cleanup.

## Read plane

```text
GET /ui/research-os/remediation/latest
```

The consolidated Research OS status also includes `research_os_remediation_latest`.

## Cockpit

The frontend page `/research-remediation` displays:

- remediation status and trust banner
- open / blocked / waived counts
- priority and category counts
- recommended commands
- remediation action queue
- warnings and blockers

## Safety posture

The remediation plan never:

- submits broker orders
- calls live broker/provider APIs
- grants ledger mutation authority
- changes `DEPLOYMENT_APPROVED`
- marks live readiness
- certifies profitability
