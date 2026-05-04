# Shadow Book Paper Portfolio

The Shadow Book is a paper-only portfolio simulator for research evidence. It persists hypothetical allocations, simulated fills, mark-to-market snapshots, drawdown, exposure, and risk flags under `artifacts/shadow_books/`.

## Non-negotiables

- No live trading.
- No broker order submission.
- No browser order controls.
- No direct ledger mutation.
- No profitability or live-readiness claim.

## CLI examples

```bash
strategy-validator-shadow-book create \
  --book-id provider-paper-demo \
  --starting-capital 100000 \
  --strategy-id momentum-SPY \
  --weight 0.25 \
  --json

strategy-validator-shadow-book simulate-day \
  --book-id provider-paper-demo \
  --date 2026-01-02 \
  --json

strategy-validator-shadow-book latest --json
```

## Artifact layout

```text
artifacts/shadow_books/{book_id}/
  shadow_book_manifest.json
  allocations/
  fills/
  daily_snapshots/
  risk_summaries/
  events/
artifacts/shadow_books/latest/
  shadow_book_manifest.json
  latest_daily_snapshot.json
  latest_risk_summary.json
```

## Risk rules

The first implementation enforces deterministic paper-only risk flags for gross exposure, max single-strategy weight, and drawdown. A blocking risk flag freezes the book by rule. Missing prices are handled by default fixture prices in demo mode; production operator use should pass explicit governed price fixtures.

## Read plane

`GET /ui/shadow-book/latest` exposes the latest manifest, daily snapshot, and risk summary. It is read-plane only and includes `no_order_controls: true`.
