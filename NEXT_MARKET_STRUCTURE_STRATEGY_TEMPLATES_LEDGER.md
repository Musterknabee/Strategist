# Next Vertical Slice — Market Structure Strategy Templates

## Objective

Add governed, OHLCV-aware market-structure strategy templates to the strategy batch runner so operators can test classic trend/momentum systems through the existing PIT, execution-realism, robustness, CPCV, evidence, and cockpit surfaces.

## Added templates

- `donchian_channel_breakout`
  - Donchian/Turtle-style channel breakout.
  - Requires a close through the prior high/low channel.
  - Holds until an opposite exit channel is breached.
  - Gates entries with volume confirmation and an ATR sanity filter.
- `atr_trailing_trend`
  - ATR trailing-stop trend-following template.
  - Uses EMA trend context plus ATR stop management.
  - Emits a persistent per-bar exposure stream for robustness gates.
- `macd_volume_momentum`
  - MACD histogram/cross momentum template.
  - Requires volume participation before entry.
  - Exits when momentum rolls over.

## Files changed

- `strategy_validator/contracts/strategy_batch.py`
- `strategy_validator/application/strategy_batch_loader.py`
- `strategy_validator/research/strategy_batch_evaluators.py`
- `configs/strategy_batches/example_market_structure_batch.json`
- `tests/fixtures/strategy_data/market_structure_bars.csv`
- `tests/research/test_market_structure_strategy_templates.py`
- `ui/strategist-web/app/strategy-lab/page.tsx`

## Validation

Focused tests:

```bash
pytest -q tests/research/test_market_structure_strategy_templates.py
```

Expected result:

```text
4 passed
```

The templates remain research/paper-only signal definitions. They do not claim profitability, do not create live order authority, and must still pass point-in-time data checks, execution realism, robustness, CPCV, parameter sensitivity, regime analysis, and paper validation before operator trust.
