# Strategy Thesis and Falsification Manifest

Strategy Thesis records the scientific claim behind a candidate before the system spends more research budget on it. The evaluator compares the thesis against gauntlet evidence and reports whether the thesis is supported, weakly supported, inconclusive, or falsified.

## Non-goals

- No live trading.
- No broker orders.
- No browser mutation controls.
- No profitability guarantee.
- No live-readiness certification.

## Thesis config

Batch strategy specs may optionally include:

```json
"thesis_path": "configs/strategy_theses/momentum_spy_thesis.json"
```

A thesis document contains:

- `strategy_id`
- `thesis_id`
- `hypothesis`
- `economic_rationale`
- `market_inefficiency`
- `expected_edge`
- `expected_regimes`
- `expected_failure_regimes`
- `required_evidence`
- `falsification_criteria`

## CLI

```bash
strategy-validator-thesis evaluate \
  --strategy-run artifacts/strategy_runs/<run-id> \
  --thesis configs/strategy_theses/momentum_spy_thesis.json \
  --json

strategy-validator-thesis list --json
```

## Read plane

```text
GET /ui/strategy-thesis/latest
```

The frontend `/thesis` page shows support status, contradictions, missing evidence, triggered falsification criteria, and raw evidence references.

## Falsification semantics

A thesis is `FALSIFIED` when a hard falsification criterion triggers, such as drawdown above the pre-committed threshold, negative performance below the minimum threshold, or a gate explicitly blocking a required evidence class.

A thesis is `INCONCLUSIVE` when required evidence is missing. Synthetic/demo data cannot strongly support a thesis.

`SUPPORTED` and `WEAKLY_SUPPORTED` are research evidence statuses only. They do not approve deployment, live trading, or capital use.
