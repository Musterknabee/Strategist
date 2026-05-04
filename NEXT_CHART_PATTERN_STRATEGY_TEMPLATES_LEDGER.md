# Next Slice Ledger — Chart Pattern Strategy Templates

## Slice

Added governed research/paper-only chart-pattern strategy templates to the strategy batch runner.

## Strategy types

- `ascending_triangle_breakout`
- `bull_flag_continuation`
- `support_resistance_retest`

## Scope

- Pydantic strategy type contract updated.
- Batch loader allow-list updated.
- Deterministic OHLCV evaluators and return-series dispatch added.
- Example chart-pattern batch config added.
- OHLCV fixture added with horizontal resistance, rising lows, bull flag, and breakout-retest structures.
- Strategy Lab UI copy and CLI examples updated.
- Focused evaluator + batch regression tests added.

## Guardrails

These are signal templates only. They do not create live order authority, do not bypass PIT/data-quality/execution-realism gates, and do not imply profitability.
