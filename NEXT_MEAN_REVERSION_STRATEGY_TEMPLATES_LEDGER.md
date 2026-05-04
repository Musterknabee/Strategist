# Next Slice Ledger — Statistical Mean-Reversion Strategy Templates

## Slice

Added governed research/paper-only OHLCV mean-reversion strategy templates to the strategy batch runner.

## Scope

Implemented three new strategy type IDs:

- `bollinger_mean_reversion`
- `vwap_deviation_reversion`
- `keltner_channel_reversion`

These templates are signal generators for the existing strategy batch evidence path. They do not add live-trading authority and must still pass PIT/data-quality/execution-realism/robustness gates before operator trust.

## Files changed

- `strategy_validator/contracts/strategy_batch.py`
  - Extended `StrategyTypeId` with the three new mean-reversion templates.
- `strategy_validator/application/strategy_batch_loader.py`
  - Added the new strategy type IDs to the explicit allowed-type registry.
- `strategy_validator/research/strategy_batch_evaluators.py`
  - Added metric evaluators and per-bar return streams for:
    - Bollinger-band RSI/volume mean reversion.
    - Rolling-VWAP deviation reversion.
    - Keltner EMA/ATR range fade.
  - Wired the new types into `strategy_returns_series()` and `evaluate_strategy_metrics()`.
- `configs/strategy_batches/example_mean_reversion_batch.json`
  - Added a governed local-bars example batch covering all three templates.
- `tests/fixtures/strategy_data/mean_reversion_bars.csv`
  - Added PIT-annotated OHLCV fixture with deterministic range-stretch/reversion regimes.
- `tests/research/test_mean_reversion_strategy_templates.py`
  - Added direct evaluator tests and full batch-run regression coverage.
- `ui/strategist-web/app/strategy-lab/page.tsx`
  - Updated Strategy Lab operator copy to advertise the new mean-reversion templates.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q strategy_validator tests/research/test_mean_reversion_strategy_templates.py
```

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/application/test_strategy_batch_loader.py \
  tests/research/test_strategy_batch_runner.py \
  tests/research/test_strategy_batch_analytics.py \
  tests/research/test_price_volume_strategy_templates.py \
  tests/research/test_advanced_technical_strategy_templates.py \
  tests/research/test_market_structure_strategy_templates.py \
  tests/research/test_mean_reversion_strategy_templates.py
```

Result: `42 passed`.

```bash
PYTHONDONTWRITEBYTECODE=1 python -m strategy_validator.cli.strategy_batch_run \
  --batch configs/strategy_batches/example_mean_reversion_batch.json \
  --output-root /tmp/sv-mean-reversion-runs \
  --run-id mean-reversion-smoke \
  --overwrite \
  --no-synthetic \
  --json
```

Result: `ok=true`, `strategy_count=3`, `passed_count=3`, `blocked_count=0`, `failed_count=0`.

## Notes

- The new templates are intentionally bounded and deterministic for paper/research evidence.
- The sample batch uses `robustness_mode=walk_forward` because mean-reversion path behavior can be distorted by the repo's current CPCV close-price heuristic; CPCV remains available but is not asserted by this sample config.
- The fixture includes `published_at_utc` to avoid claiming PIT verification without release-time metadata.
