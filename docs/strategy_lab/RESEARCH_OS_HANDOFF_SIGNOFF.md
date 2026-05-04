# Research OS Handoff Verification and Reviewer Signoff

The Research OS handoff-signoff layer verifies the latest single-tenant handoff pack and records a reviewer-facing signoff artifact.

This is **not deployment approval**. It does not enable live trading, submit broker orders, expose browser order controls, mutate the ledger, or certify profitability.

## What it verifies

The verifier checks:

- the latest `research_os_handoff_pack.json` exists;
- the handoff pack `manifest_sha256` still matches its current contents;
- the handoff pack `handoff_spine_sha256` still matches its current checklist/source-ref spine;
- each source artifact referenced by the handoff pack is still present;
- referenced source artifact `manifest_sha256` values still match the values captured in the handoff pack;
- no known secret markers are present in the handoff pack or source artifacts;
- safety flags remain non-trading and read-plane-only.

## Commands

Build verification evidence:

```bash
strategy-validator-research-os-handoff-signoff verify \
  --artifact-root artifacts \
  --verification-id daily-handoff-verification \
  --write \
  --overwrite \
  --json
```

Record reviewer signoff:

```bash
strategy-validator-research-os-handoff-signoff signoff \
  --artifact-root artifacts \
  --signoff-id daily-handoff-signoff \
  --reviewer-id local-reviewer \
  --decision ACCEPTED_WITH_RESTRICTIONS \
  --rationale "Single-tenant handoff reviewed; not deployment approval" \
  --constraint "No live trading" \
  --overwrite \
  --json
```

Read latest:

```bash
strategy-validator-research-os-handoff-signoff latest --artifact-root artifacts --json
```

Demo:

```bash
python scripts/run_research_os_handoff_signoff_demo.py \
  --artifact-root artifacts \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_handoff_signoff/
  verifications/{verification_id}/research_os_handoff_verification_result.json
  signoffs/{signoff_id}/research_os_handoff_reviewer_signoff.json
  latest/research_os_handoff_verification_result.json
  latest/research_os_handoff_reviewer_signoff.json
```

## Status vocabulary

Verification status:

- `VERIFIED`: handoff and source-ref digests match.
- `STALE`: handoff is internally consistent but carries restricted/stale warnings.
- `TAMPERED`: digest mismatch, secret marker, or safety flag violation was detected.
- `MISSING`: handoff pack is absent.
- `BLOCKED`: verification cannot be trusted due blocking evidence.

Reviewer decision:

- `ACKNOWLEDGED`: reviewer acknowledged a verified ready handoff.
- `ACCEPTED_WITH_RESTRICTIONS`: reviewer accepted a verified/restricted handoff for review only.
- `REJECTED`: reviewer rejected the handoff.
- `BLOCKED`: verification did not permit signoff.

## Cockpit

Read-plane route:

```text
GET /ui/research-os/handoff-signoff/latest
```

Frontend route:

```text
/research-handoff-signoff
```

## Limitations

The signoff artifact is a reviewer record. It does not change `DEPLOYMENT_APPROVED`, does not authorize capital, and does not claim live readiness.
