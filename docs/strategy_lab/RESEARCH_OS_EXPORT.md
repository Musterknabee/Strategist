# Research OS Export Bundle

The Research OS export bundle is a portable, offline evidence handoff for the operator. It copies already-produced Research OS artifacts into a bundle directory, records SHA-256 digests, optionally creates a `.tar.gz`, and exposes the latest bundle through the UI read-plane.

This is **not** live trading, broker execution, deployment approval, or profitability certification.

## What it packages

The exporter looks for the latest available evidence under the artifact root, including:

- Research OS briefing pack
- Research OS closure manifest
- closure verification result
- operator attestation
- provider-backed paper loop manifest
- provider historical snapshot run
- paper broker policy status
- latest strategy batch summary
- latest market-data integrity result
- strategy memory index
- strategy thesis evaluation
- shadow book manifest and risk summary
- Research OS runtime manifest

Required artifacts for an unrestricted export are:

- briefing pack
- closure manifest
- closure verification result
- operator attestation

Missing optional artifacts are recorded as warnings. Missing required artifacts block the export.

## Build

```bash
strategy-validator-research-os-export build \
  --export-id daily-research-export \
  --overwrite \
  --json
```

Host script:

```bash
python scripts/run_research_os_export_demo.py \
  --artifact-root artifacts \
  --export-id research-os-export-demo \
  --overwrite \
  --json
```

## Verify

```bash
strategy-validator-research-os-export verify --json
```

Verification checks that every copied bundle file still matches the digest captured in the export manifest. A changed or missing copied file becomes a blocker.

## Artifact layout

```text
artifacts/research_os_exports/
  exports/{export_id}/
    bundle/
      evidence/...
      research_os_export_manifest.json
    {export_id}.tar.gz
    research_os_export_manifest.json
  latest/
    research_os_export_manifest.json
    research_os_export_verification.json
    {export_id}.tar.gz
```

## Read-plane

```text
GET /ui/research-os/export/latest
```

The Research OS status payload also includes:

```text
research_os_export_latest
```

## Safety posture

The exporter is offline and read-only. It does not:

- call provider networks
- access broker order endpoints
- submit orders
- mutate the ledger
- grant deployment approval
- make profitability claims
- expose secrets intentionally

Known secret marker strings are scanned in exported text artifacts. A hit blocks the export.
