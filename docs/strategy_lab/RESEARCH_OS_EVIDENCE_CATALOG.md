# Research OS Evidence Catalog

The Research OS Evidence Catalog is a read-plane index over already-produced Research OS artifacts.
It answers the operator question: **what evidence exists, where is it, what category does it belong to, and what SHA-256 digest identifies it?**

It does not run research, call provider APIs, contact brokers, submit orders, mutate the ledger, approve deployment, or certify profitability.

## What it indexes

The catalog scans the configured artifact root for known Research OS artifacts, including:

- operator run manifests
- export manifests, export verification results, and export archives
- briefing packs
- closure manifests
- closure verification and operator attestation artifacts
- provider paper loop manifests
- provider historical snapshot runs
- paper broker policy status artifacts
- strategy batch summaries
- market data integrity results
- strategy memory indexes
- thesis evaluations
- shadow book manifests and risk summaries
- runtime demo manifests

Each entry records:

- category
- artifact path and path relative to the artifact root
- SHA-256 digest
- file size
- observed schema version
- status/trust/ok hints when present
- warning/blocker hints when present
- whether the entry is a `latest/` alias

## CLI

Build the catalog:

```bash
strategy-validator-research-os-catalog build \
  --catalog-id daily-catalog \
  --artifact-root artifacts \
  --overwrite \
  --json
```

Read the latest catalog:

```bash
strategy-validator-research-os-catalog latest \
  --artifact-root artifacts \
  --json
```

Host script:

```bash
python scripts/run_research_os_evidence_catalog_demo.py \
  --artifact-root artifacts \
  --catalog-id research-os-evidence-catalog-demo \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_evidence_catalog/
  catalogs/{catalog_id}/research_os_evidence_catalog.json
  latest/research_os_evidence_catalog.json
  latest/latest_ref.json
```

## Read-plane

```text
GET /ui/research-os/catalog/latest
```

The consolidated Research OS status payload also includes:

```text
research_os_evidence_catalog_latest
```

Frontend cockpit page:

```text
/research-catalog
```

## Status semantics

- `READY`: catalog built and no indexed warnings/blockers were detected.
- `RESTRICTED`: catalog built, but indexed artifacts carry warnings, missing-evidence hints, degraded status, or policy restrictions.
- `BLOCKED`: catalog found an unreadable JSON artifact or a configured secret-marker string in an indexed file.
- `EMPTY`: no known Research OS evidence artifacts were found.

`RESTRICTED` is normal for partial/demo roots. It is not a runtime failure; it means the catalog is honest about incomplete evidence.

## Safety boundaries

The catalog is strictly read-plane/evidence-plane infrastructure:

- no live trading
- no broker orders
- no browser order controls
- no ledger mutation
- no deployment approval mutation
- no profitability claim
- no provider network access

If a secret marker is detected in an indexed artifact, the catalog becomes `BLOCKED` and the marker is reported only as a blocker label, not as a secret value.
