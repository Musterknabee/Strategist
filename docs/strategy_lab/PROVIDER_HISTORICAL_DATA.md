# Provider historical data ingestion

**Scope:** Research/paper bar snapshots only. **Not live trading.** Freemium/vendor licensing is operator responsibility.

## Behavior

- Optional: backend and tests **never require** provider keys.
- Missing keys → `PENDING_KEY` / degraded manifest — **not** fake success.
- Bars are written to local CSV under `artifacts/strategy_data/...` before any batch consumes them.
- PIT status is explicit (`MISSING_RELEASE_TIMESTAMPS` / `BEST_EFFORT_AS_OF` for typical vendor daily JSON).

## CLI

```bash
strategy-validator-provider-bars ingest \
  --provider tiingo \
  --symbol SPY \
  --timeframe 1d \
  --start 2024-01-01 \
  --end 2024-12-31 \
  --as-of 2025-01-01T00:00:00Z \
  --output-root artifacts/strategy_data \
  --env-file deployment.env \
  --json
```

Supported provider IDs include `tiingo` and `alpha_vantage` (keys from env).

## Read-plane / UI

Provider health remains on `GET /ui/provider-health`. Strategist **Providers** page documents the CLI path for historical snapshots.

## Limitations

Vendor data is research-grade unless your license/trust model says otherwise. No claim of PIT-verified corporate actions without separate evidence.

## Next graduation step

Wire batch `data_source` to governed local snapshots produced by this CLI; keep manifests and SHA digests in evidence bundles.
