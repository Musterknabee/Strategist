# Next Slice Ledger — Price/Volume Strategy Templates

## Slice

Added research/paper-only strategy templates that can read OHLCV bars rather than only close-price paths:

1. `moving_average_trend`
   - Fast/slow moving-average trend alignment.
   - Optional volume confirmation via `volume_window` + `min_volume_ratio`.

2. `trendline_volume_breakout`
   - Detects diagonal resistance/support candidates from swing highs/lows.
   - Falls back to conservative horizontal support/resistance when pivots are insufficient.
   - Requires close breakout plus volume expansion confirmation.

3. `obv_accumulation_breakout`
   - Uses on-balance-volume accumulation confirmation.
   - Requires price breakout, OBV confirmation, and volume participation.

## Guardrail

These templates are not profitability claims and do not enable live trading. They are deterministic strategy candidates for the existing governed strategy-batch pipeline, so they still pass through PIT, data-quality, market-data-integrity, execution-realism, robustness, CPCV, parameter-sensitivity, regime-analysis, ranking, and evidence-manifest gates.

## Repo Surfaces Changed

- `strategy_validator/contracts/strategy_batch.py`
  - Extended `StrategyTypeId`.
  - Added optional `strategy_type` to run results and evidence manifests.

- `strategy_validator/research/strategy_batch_evaluators.py`
  - Added OHLCV-aware evaluator dispatch.
  - Added MA trend, diagonal trendline breakout, and OBV accumulation breakout return/metric functions.

- `strategy_validator/research/strategy_batch_runner.py`
  - Extracts high/low/volume arrays from governed local/provider bars.
  - Routes all strategy types through the evaluator dispatch.
  - Writes strategy type into run/evidence artifacts.

- `strategy_validator/research/strategy_batch_analytics.py`
  - Uses the shared strategy return-series dispatch so charts reflect the selected strategy type.

- `strategy_validator/research/strategy_parameter_sensitivity.py`
  - Evaluates perturbations through the same strategy dispatch.

- `strategy_validator/research/strategy_regime_analysis.py`
  - Uses the shared dispatch for regime attribution.

- `strategy_validator/application/strategy_batch_loader.py`
  - Allows the new strategy identifiers.

- `configs/strategy_batches/example_price_volume_batch.json`
  - Added a concrete batch example for the new OHLCV templates.

- `tests/fixtures/strategy_data/price_volume_breakout_bars.csv`
  - Added deterministic PIT-friendly local bars with a breakout/volume expansion regime.

- `tests/research/test_price_volume_strategy_templates.py`
  - Added direct evaluator and end-to-end batch-run coverage.

- `ui/strategist-web/app/strategy-lab/page.tsx`
  - Strategy Lab now displays strategy type and points the command snippet to the price/volume example batch.

## Validation

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q strategy_validator tests/research/test_price_volume_strategy_templates.py

PYTHONDONTWRITEBYTECODE=1 pytest -q \
  tests/application/test_strategy_batch_loader.py \
  tests/research/test_strategy_batch_runner.py \
  tests/research/test_strategy_batch_analytics.py \
  tests/research/test_price_volume_strategy_templates.py
```

Result: `30 passed`

Smoke:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m strategy_validator.cli.strategy_batch_run \
  --batch configs/strategy_batches/example_price_volume_batch.json \
  --output-root /tmp/sv-price-volume-runs \
  --run-id price-volume-smoke \
  --overwrite \
  --no-synthetic \
  --json
```

Result: `strategy_count=3`, `passed_count=3`, `failed_count=0`, `paper_only_count=0`, `ok=true`.
