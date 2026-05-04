# Next Slice Ledger — Oracle Strategy Thesis Generation

## Slice

Adds a deterministic, advisory-only Oracle strategy thesis generator that converts existing `strategy_batch_run_summary/v1` evidence into falsification-first `strategy_thesis/v1` artifacts and optional immediate thesis evaluations.

## Why

The repository already had strategy batch testing and manual thesis evaluation. This slice closes the gap between those surfaces: Oracle can now propose durable research theses from evidence without gaining live-trading, capital, or ledger-mutation authority.

## Implemented

- New thesis generation contracts:
  - `GeneratedStrategyThesisArtifact`
  - `StrategyThesisGenerationReport`
- New deterministic generator:
  - `strategy_validator/research/strategy_thesis_generator.py`
- CLI extension:
  - `strategy-validator-thesis generate-from-batch --strategy-run <batch_summary_or_run_dir> --json`
- UI read-plane route:
  - `/ui/strategy-thesis/generation/latest`
- Frontend hook/page wiring:
  - generated thesis count, evaluation count, report digest, and latest generated thesis statuses
- Tests:
  - generator unit/application coverage
  - CLI round-trip coverage

## Authority boundary

- Read-plane/advisory only.
- No live trading.
- No order submission.
- No validator ledger mutation.
- Generated theses remain hypotheses until independently validated and operator-reviewed.

## Validation target

- Python compile for changed modules/tests.
- Focused pytest coverage for thesis generation and CLI.
- CLI smoke via a real strategy batch summary when feasible.
