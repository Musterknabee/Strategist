# Portfolio allocation simulator

**Scope:** Deterministic research/paper weighting across batch scorecards. **No orders.** **Not an optimizer.**

## CLI

```bash
strategy-validator-portfolio-sim \
  --batch-run artifacts/strategy_runs/<batch_id>/<run_id> \
  --capital 100000 \
  --method capped_score_weight \
  --json
```

Writes `portfolio_allocation_result.json` next to `batch_summary.json`.

## Methods

`equal_weight`, `inverse_volatility`, `risk_budget`, `capped_score_weight` (see `strategy_validator/contracts/portfolio_allocation.py`).

Blocked / synthetic strategies are excluded by default; duplicative IDs can be capped via request fields.

## Read-plane / UI

`GET /ui/strategy-batches/latest` (and detail) includes `portfolio_allocation` when the artifact exists.

## Limitations

Correlation clustering warnings are heuristic; volatility and drawdown proxies come from scorecards, not a full risk engine.

## Next graduation step

Treat outputs as scenario evidence; keep capital markets compliance review outside this tool.
