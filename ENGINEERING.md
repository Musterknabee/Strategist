# Engineering note: constitutional layout

## Package ownership

| Area | Role |
| --- | --- |
| `strategy_validator.core` | Taxonomy, enums, exceptions, manifest hashing. |
| `strategy_validator.contracts` | Typed cross-layer DTOs (experiments, evidence, tribunal, benchmarks). |
| `strategy_validator.proposers` | Proposal-only code; client of contracts/core/api. |
| `strategy_validator.tribunal` | Semantic / constraint proposals; no validator or ledger writer. |
| `strategy_validator.feature_factory` | PIT and market features; must not import `validator`. |
| `strategy_validator.validator` | Gates, engines, orchestration. |
| `strategy_validator.validator.orchestrator` | Sole production adjudication path that calls `ledger.writer`. |
| `strategy_validator.ledger.reader` | Read-only lineage access. |
| `strategy_validator.ledger.writer` | Append-only writes; only orchestrator should call `commit_state_transition` in production. |
| `strategy_validator.api` | Transport-thin surface; no adjudication or persistence. |

## Allowed import directions (summary)

- **Proposers**: `core`, `contracts`, `api`, and intra-package `proposers.*` only (enforced by tests + import-linter).
- **Tribunal**: must not import `validator` or `ledger.writer` (tests + import-linter).
- **Feature factory**: must not import `validator` (tests + import-linter).
- **Validator**: may use `contracts`, `core`, `feature_factory`, `ledger.reader`, `ledger.writer` only where architecturally intended; **only `validator.orchestrator` imports `ledger.writer`** (AST tests).
- **API**: keep thin; no ledger writes.

## Who may write the ledger

- **Writer module** (`ledger.writer`): performs appends via internal `_append_only` store.
- **Production policy**: `validator.orchestrator.adjudicate` is the only intended callsite for `commit_state_transition` (see `tests/constitutional/test_write_surface.py`).

## Why `feature_factory` is separate from `tribunal`

- **Tribunal** proposes structured semantic judgments and constraints; it must not see validation outcomes or import adjudication stacks (bias / self-certification risk).
- **Feature_factory** materializes point-in-time and market-state features; it is a data layer and must not **adjudicate** strategy success (no `validator` imports). Tribunal output may feed features, but features alone do not certify promotion.
