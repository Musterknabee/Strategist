# Research OS Review Journal

The Research OS review journal is a local, digest-linked review record over already-produced Research OS evidence. It summarizes policy gate, governed exception, remediation, release-readiness, handoff, and reviewer signoff artifacts into a single read-plane journal.

It is **not** the canonical validator ledger. It does not mutate the append-only decision ledger, does not approve deployment, does not enable live trading, does not submit broker orders, and does not certify profitability.

## Build

```bash
strategy-validator-research-os-review-journal build \
  --artifact-root artifacts \
  --journal-id daily-review-journal \
  --overwrite \
  --json
```

Or run the demo wrapper:

```bash
python scripts/run_research_os_review_journal_demo.py \
  --artifact-root artifacts \
  --journal-id review-journal-demo \
  --overwrite \
  --json
```

## Artifact layout

```text
artifacts/research_os_review_journal/
  journals/{journal_id}/research_os_review_journal.json
  latest/research_os_review_journal.json
  latest/latest_ref.json
```

## Read-plane

```text
GET /ui/research-os/review-journal/latest
```

The Research OS aggregate status also includes:

```text
research_os_review_journal_latest
```

## Status semantics

- `READY`: all indexed review artifacts are present without warnings/blockers.
- `RESTRICTED`: artifacts exist, but at least one source is restricted, stale, warned, or partially degraded.
- `BLOCKED`: a source artifact has a blocker, false safety flag, secret marker, or deployment-approved flag.
- `EMPTY`: no review source artifacts were found.

## Safety invariants

The journal preserves these invariants:

- read-plane only
- no live trading
- no broker orders
- no browser order controls
- no profitability claim
- `deployment_approved` remains false
- `DEPLOYMENT_APPROVED` semantics are unchanged
