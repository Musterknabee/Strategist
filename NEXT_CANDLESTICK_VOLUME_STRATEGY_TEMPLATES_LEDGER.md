# Next Slice Ledger — Candlestick + Volume Strategy Templates

## Scope

Added three governed research/paper-only OHLCV strategy templates that require open/high/low/close/volume data:

- `bullish_engulfing_volume_reversal`
- `hammer_volume_reversal`
- `inside_bar_volume_breakout`

The slice extends the strategy batch runner from close-only technical templates into open/close candlestick semantics while preserving the repo posture: no live authority, no profitability guarantee, and all candidates remain subject to PIT, data quality, execution realism, robustness, parameter sensitivity, regime analysis, and evidence artifact generation.

## Files changed

- `strategy_validator/contracts/strategy_batch.py`
- `strategy_validator/application/strategy_batch_loader.py`
- `strategy_validator/research/strategy_batch_evaluators.py`
- `strategy_validator/research/strategy_batch_runner.py`
- `strategy_validator/research/strategy_batch_analytics.py`
- `strategy_validator/research/strategy_parameter_sensitivity.py`
- `strategy_validator/research/strategy_regime_analysis.py`
- `configs/strategy_batches/example_candlestick_volume_batch.json`
- `tests/fixtures/strategy_data/candlestick_volume_bars.csv`
- `tests/research/test_candlestick_volume_strategy_templates.py`
- `ui/strategist-web/app/strategy-lab/page.tsx`

## Validation target

- Compile strategy validator modules.
- Direct evaluator tests prove each candle/volume template emits the intended paper signal on deterministic OHLCV fixture data.
- Batch runner test proves all three strategy types pass through governed local-bar evidence generation without synthetic fallback.
- CLI smoke command proves the example config runs from the public CLI.

## Non-goals

- No live trading authority.
- No claim that candlestick patterns are profitable by themselves.
- No bypass around strategy promotion gates.
