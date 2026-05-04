# Research OS Briefing Pack

The Research OS briefing pack is a read-plane/operator artifact that summarizes the current evidence posture after closure and attestation.

It is designed for daily review of a personal/single-tenant research system. It does **not** authorize live trading, broker orders, deployment approval, or profitability claims.

## What it does

The briefing builder scans the configured artifact root and packages the latest available evidence into one digest-linked JSON artifact:

- Research OS closure manifest
- Closure verification result
- Operator attestation
- Provider-backed paper loop manifest
- Provider historical snapshot run
- Paper broker policy/status
- Latest strategy batch summary, if present
- Strategy memory / graveyard index
- Thesis / falsification evaluation
- Shadow book manifest and risk summary
- Runtime demo manifest

Each section records status, artifact path, digest, selected key fields, warnings, and blockers. The pack also emits operator action items such as commands to build missing closure, verification, attestation, provider loop, or shadow-book artifacts.

## Artifact layout

```text
artifacts/research_os_briefings/
  briefings/{briefing_id}/research_os_briefing_pack.json
  latest/research_os_briefing_pack.json
```

## CLI

Build a briefing pack:

```bash
strategy-validator-research-os-briefing build \
  --briefing-id daily-research-briefing \
  --overwrite \
  --json
```

Read latest payload:

```bash
strategy-validator-research-os-briefing latest --json
```

Host script:

```bash
python scripts/run_research_os_briefing_demo.py \
  --artifact-root artifacts \
  --briefing-id research-os-briefing-demo \
  --overwrite \
  --json
```

## API / cockpit

Read-plane route:

```text
GET /ui/research-os/briefing/latest
```

Frontend page:

```text
/research-briefing
```

Research OS status also includes:

```text
research_os_briefing_latest
```

## Status semantics

- `READY`: closure is verified and operator attestation is present.
- `RESTRICTED`: evidence exists but needs review.
- `BLOCKED`: required evidence is missing, unreadable, or invalid.
- `EMPTY`: no meaningful Research OS evidence exists.

Trust banners are inherited from closure/verification posture where possible:

- `TRUSTED`
- `TRUST_RESTRICTED`
- `UNTRUSTED`

## Safety boundaries

The briefing pack is evidence-only:

- no live trading
- no broker orders
- no browser order controls
- no API tokens in browser payloads
- no direct ledger mutation
- no profitability certification
- no deployment approval

`PENDING_KEY`, missing provider artifacts, and missing broker artifacts are operator warnings/action items, not hidden startup failures.
