# Research OS Closure Manifest

The Research OS closure manifest is a paper-only, read-plane evidence spine for the local research operating system. It records which subsystem artifacts were present at close, whether they were readable JSON, their SHA-256 file digests, source schema hints, warnings, blockers, and an overall trust banner.

It does **not** approve deployment. It does **not** authorize live trading. It does **not** submit or enable broker orders. It does **not** certify profitability.

## What it closes

The closure builder scans the configured artifact root for the latest known Research OS evidence surfaces, including:

- provider-backed paper loop manifest
- provider historical snapshot run
- paper broker policy/status artifact
- latest strategy batch summary
- latest market-data integrity result, when attached to a batch
- strategy memory index
- strategy thesis evaluation
- shadow book manifest and risk summary
- Research OS runtime demo manifest

Missing artifacts are represented as degraded evidence rather than API failure. Paper broker `PENDING_KEY` and provider `PENDING_KEY` are policy/status warnings, not startup failures.

## CLI

```bash
strategy-validator-research-os-closure build \
  --closure-id daily-research-close \
  --overwrite \
  --json
```

Host script:

```bash
python scripts/run_research_os_closure_demo.py \
  --artifact-root artifacts \
  --closure-id research-os-closure-demo \
  --overwrite \
  --json
```

The latest read-plane payload is available via:

```bash
strategy-validator-research-os-closure latest --json
```

## Artifact layout

```text
artifacts/research_os_closure/{closure_id}/research_os_closure_manifest.json
artifacts/research_os_closure/latest/research_os_closure_manifest.json
artifacts/research_os_closure/latest/latest_ref.json
```

## API and cockpit

The API exposes:

```text
GET /ui/research-os/closure/latest
```

The frontend cockpit exposes a Research Closure page at:

```text
/research-closure
```

`/research-os` also includes a closure panel when the manifest exists.

## Status and trust banners

Closure status:

- `COMPLETE` — expected evidence is present and no warnings/blockers were observed.
- `DEGRADED` — useful evidence exists, but at least one subsystem is missing, pending, or warning.
- `BLOCKED` — one or more blocker statuses, unreadable artifacts, or secret markers were detected.
- `EMPTY` — no known Research OS artifacts were present.

Trust banner:

- `TRUSTED` — complete digest-linked closure without warnings/blockers.
- `TRUST_RESTRICTED` — digest-linked closure exists but has missing/pending/warning evidence.
- `UNTRUSTED` — no evidence or blocking evidence.

## Safety boundaries

- read-plane only
- no live trading
- no broker orders
- no browser order controls
- no API tokens or provider secrets in closure artifacts
- deployment approval semantics unchanged
