# Next Vertical Slice Ledger — Advanced Technical Strategy Templates

## Slice

Implemented an end-to-end research/paper feature slice for advanced OHLCV technical strategy templates.

## New strategy templates

- `rsi_volume_reversal`
  - RSI exhaustion / recovery template.
  - Requires volume expansion confirmation.
  - Long-only by default; optional short branch remains parameter-gated.
- `bollinger_squeeze_breakout`
  - Compression / expansion template using Bollinger-band width.
  - Requires breakout beyond prior-band envelope and volume confirmation.
- `vwap_pullback_continuation`
  - Rolling-VWAP pullback/reclaim continuation template.
  - Requires trend context, VWAP reclaim, and volume participation.

## Changed surfaces

- `strategy_validator/contracts/strategy_batch.py`
  - Extended `StrategyTypeId` with the three new paper/research strategy IDs.
- `strategy_validator/application/strategy_batch_loader.py`
  - Added the new IDs to the supported batch loader allow-list.
- `strategy_validator/research/strategy_batch_evaluators.py`
  - Added deterministic OHLCV helpers and evaluator/return-series implementations.
  - Wired the new strategies through `evaluate_strategy_metrics` and `strategy_returns_series`.
- `configs/strategy_batches/example_advanced_technical_batch.json`
  - Added a complete runnable paper batch over governed local OHLCV fixtures.
- `tests/fixtures/strategy_data/advanced_technical_bars.csv`
  - Added deterministic PIT-friendly OHLCV fixture with squeeze, pullback, and exhaustion/recovery regimes.
- `tests/research/test_advanced_technical_strategy_templates.py`
  - Added direct evaluator tests and end-to-end batch runner regression coverage.
- `ui/strategist-web/app/strategy-lab/page.tsx`
  - Added Strategy Lab operator copy for the advanced strategy templates and a runnable CLI example.

## Guardrails

- These templates are research/paper-only signal templates.
- They do not claim profitability.
- They continue to rely on the existing gates: PIT validity, data quality, market-data integrity, robustness, CPCV, parameter sensitivity, regime analysis, and execution realism.
- The batch fixture uses governed local bars and `--no-synthetic` in the UI example.

## Validation

Focused validation completed:

```bash
PYTHONDONTWRITEBYTECODE=1 python -m compileall -q strategy_validator tests/research/test_advanced_technical_strategy_templates.py

pytest -q \
  tests/application/test_strategy_batch_loader.py \
  tests/research/test_strategy_batch_runner.py \
  tests/research/test_strategy_batch_analytics.py \
  tests/research/test_price_volume_strategy_templates.py \
  tests/research/test_advanced_technical_strategy_templates.py
```

CLI smoke:

```bash
python -m strategy_validator.cli.strategy_batch_run \
  --batch configs/strategy_batches/example_advanced_technical_batch.json \
  --output-root /tmp/sv-advanced-technical-runs \
  --run-id advanced-technical-smoke \
  --overwrite \
  --no-synthetic \
  --json
```
