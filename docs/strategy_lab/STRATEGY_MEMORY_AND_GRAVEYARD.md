# Strategy Memory and Candidate Graveyard

Strategy Memory is a research-governance artifact layer. It records strategy families, variants, lifecycle outcomes, failure reasons, duplicate-variant warnings, and graveyard entries so the operator does not repeatedly rediscover the same fragile or killed ideas.

## Non-goals

- No live trading.
- No broker orders.
- No profitability guarantee.
- No direct ledger writer import.
- No browser mutation controls.

## Artifact layout

```text
artifacts/strategy_memory/
  memory_index.json
  latest/memory_index.json
  families/{family_id}.json
  variants/{strategy_id}.json
  graveyard/{strategy_id}.json
```

## CLI

```bash
strategy-validator-strategy-memory ingest-batch \
  --batch-run artifacts/strategy_runs/<run-id> \
  --json

strategy-validator-strategy-memory ingest-paper \
  --tracking-id <tracking-id> \
  --json

strategy-validator-strategy-memory build-index --json
strategy-validator-strategy-memory list-graveyard --json
```

## Read plane

```text
GET /ui/strategy-memory/latest
```

The payload includes active, killed, rejected, duplicate warning, family counts, top failure reasons, recent graveyard entries, duplicate-variant warnings, and memory records.

## Failure reasons

The initial deterministic classifier maps batch gates and lifecycle evidence to:

- `DATA_QUALITY`
- `PIT`
- `EXECUTION_REALISM`
- `ROBUSTNESS`
- `PARAMETER_FRAGILITY`
- `REGIME_FAILURE`
- `PORTFOLIO_DUPLICATIVE`
- `PAPER_DECAY`
- `KILL_RULE`
- `INSUFFICIENT_EVIDENCE`
- `OPERATOR_REJECTED`

## Duplicate-variant warning

Similarity is advisory. It warns when a candidate shares enough lineage traits with an existing candidate, such as same strategy type and universe, identical normalized parameter fingerprint, identical provider snapshot digest, or overlapping family tags.

The warning does not hard-block research by itself. It gives the operator a reason to inspect before spending more research budget.
