# Research OS Evidence Drift

The Research OS Evidence Drift report compares two Research OS evidence catalogs and records what changed between them.

It is designed for operator review after catalog generation:

```text
closure → attestation → briefing → export → operator run → evidence catalog → evidence drift
```

## What it does

The drift report compares catalog entries by category and relative artifact path. It records:

- added artifacts
- removed artifacts
- changed artifacts
- unchanged artifacts
- digest changes
- status/trust movement
- size deltas
- category-level change counts
- warnings and blockers inherited from the compared catalogs

## What it does not do

It does **not**:

- execute research
- call market-data providers
- call broker APIs
- submit broker orders
- mutate the ledger
- approve deployment
- certify profitability
- grant live-trading authority

## CLI

Build a drift report using the latest two catalogs when available:

```bash
strategy-validator-research-os-drift build \
  --artifact-root artifacts \
  --drift-id daily-drift \
  --overwrite \
  --json
```

Compare explicit catalogs:

```bash
strategy-validator-research-os-drift build \
  --baseline-catalog artifacts/research_os_evidence_catalog/catalogs/yesterday/research_os_evidence_catalog.json \
  --candidate-catalog artifacts/research_os_evidence_catalog/catalogs/today/research_os_evidence_catalog.json \
  --artifact-root artifacts \
  --drift-id today-vs-yesterday \
  --overwrite \
  --json
```

Read the latest report:

```bash
strategy-validator-research-os-drift latest --artifact-root artifacts --json
```

Host/demo wrapper:

```bash
python scripts/run_research_os_evidence_drift_demo.py \
  --artifact-root artifacts \
  --drift-id evidence-drift-demo \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_drift/
  reports/{drift_id}/research_os_drift_report.json
  latest/research_os_drift_report.json
  latest/latest_ref.json
```

## Read-plane

```text
GET /ui/research-os/drift/latest
```

The consolidated Research OS status also includes:

```text
research_os_evidence_drift_latest
```

## Frontend cockpit

The operator console page is:

```text
/research-drift
```

It shows drift status, trust banner, baseline/candidate catalog IDs, added/removed/changed/unchanged counts, category deltas, warnings, blockers, and changed evidence entries.

## Status semantics

- `READY`: no drift and no inherited warnings/blockers.
- `RESTRICTED`: drift exists, only one catalog exists, or compared catalogs carry warnings/degraded status.
- `BLOCKED`: an unreadable/invalid catalog or blocker is present.
- `EMPTY`: no candidate catalog exists.

`RESTRICTED` is normal when comparing a partial Research OS artifact root or when only a self-baseline is available.
