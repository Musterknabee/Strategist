# Research OS Release Readiness

`Research OS Release Readiness` is a read-plane review artifact that summarizes whether the latest Research OS evidence is ready for a **single-tenant release review**.

It is deliberately **not** deployment approval. It does not enable live trading, broker orders, browser order controls, ledger mutation authority, or profitability claims.

## Inputs

The report consumes existing local evidence only:

- `research_os_policy_gate/latest/research_os_policy_gate_report.json`
- `research_os_exceptions/latest/research_os_exception_record.json`
- `research_os_remediation/latest/research_os_remediation_plan.json`
- `research_os_operator_runs/latest/research_os_operator_run_manifest.json`
- `research_os_evidence_catalog/latest/research_os_evidence_catalog.json`
- `research_os_drift/latest/research_os_drift_report.json`
- closure, attestation, briefing, and export artifacts when present

## Output

```text
artifacts/research_os_release_readiness/
  reports/{report_id}/research_os_release_readiness_report.json
  latest/research_os_release_readiness_report.json
  latest/latest_ref.json
```

## Decisions

- `SINGLE_TENANT_REVIEW_READY` — evidence is ready for release review only.
- `REVIEW_WITH_RESTRICTIONS` — review may proceed with explicit restrictions.
- `REMEDIATION_REQUIRED` — open remediation prevents review readiness.
- `BLOCKED_BY_EVIDENCE` — hard evidence blockers exist.
- `NO_EVIDENCE` — required Research OS evidence is absent.

## CLI

```bash
strategy-validator-research-os-release-readiness build \
  --artifact-root artifacts \
  --report-id daily-release-review \
  --overwrite \
  --json

strategy-validator-research-os-release-readiness latest \
  --artifact-root artifacts \
  --json
```

Demo wrapper:

```bash
python scripts/run_research_os_release_readiness_demo.py \
  --artifact-root artifacts \
  --report-id release-readiness-demo \
  --overwrite \
  --json
```

## Cockpit

The read-plane route is:

```text
GET /ui/research-os/release-readiness/latest
```

The frontend route is:

```text
/research-release-readiness
```

## Safety rules

- `deployment_approved` is always false in this artifact.
- `deployment_approval_unchanged` must remain true.
- `no_live_trading`, `no_broker_orders`, `no_order_controls`, and `no_profitability_claim` must remain true.
- P0/P1 remediation items prevent review readiness.
- A `WARN` policy gate requires an active governed exception to be reviewable.
- A `BLOCK` policy gate cannot be bypassed by this report.
