# Paper tracking (research evidence)

Operator map for the whole research stack: **[RESEARCH_OPERATING_SYSTEM.md](./RESEARCH_OPERATING_SYSTEM.md)**.

## Purpose

Paper tracking extends the **research gauntlet** into a **governed paper posture**: enrolled strategies accumulate **deterministic evidence artifacts** (daily signal snapshots, realized outcome snapshots, scorecards, kill-rule evaluation) **without live trading**, **without broker orders**, and **without ledger mutation** from the paper tracker.

**Status:** research / operator evidence plane only. Does **not** change **DEPLOYMENT_APPROVED** semantics.

## Rules

1. **No live trading** — no order routing or venue integration in this module.
2. **No broker orders** — outcomes are **mark-to-model** from evidence, not broker fills.
3. **No ledger mutation** — `paper_tracking_ops` does not import `ledger.writer`.
4. **Evidence / artifact based** — all state is JSON under `artifacts/paper_tracking/`.
5. **Synthetic strategies** — only enroll with **`--allow-synthetic-demo`**; posture is **`DEMO_PAPER_ONLY`** (not production proof) and they **never** reach **`PROMOTION_REVIEW_READY`**.
6. **Portfolio DUPLICATIVE** — batch **`portfolio_correlation_summary`** warnings and gate status are **copied into the manifest** and **surface on the scorecard** as carry-forward warnings. **`PROMOTION_REVIEW_READY`** is blocked while the manifest carry-forward gate is **`DUPLICATIVE`** unless **`governance.allow_promotion_despite_duplicative`** is set with a **non-empty** **`duplicative_promotion_rationale`** (via **`paper-track assess`** flags or a controlled manifest edit).
7. **Read-plane** — HTTP routes are GET-only; Strategy Lab / Paper page is **read-plane** (enroll / assess via CLI).

## Enrollment eligibility

- **Real local bars:** `PASSED`, **`promotion_eligible`** from gauntlet, not synthetic data plane.
- **Synthetic demo:** `PAPER_ONLY` + synthetic plane, only if **`--allow-synthetic-demo`**.

## CLI

Console entry point (after `pip install .`):

```bash
strategy-validator-paper-track enroll --batch-run path/to/batch/run/dir [--strategy-id ID ...] [--allow-synthetic-demo] [--json]
strategy-validator-paper-track snapshot --tracking-id TRACKING_ID [--as-of YYYY-MM-DD] [--json]
strategy-validator-paper-track evaluate --tracking-id TRACKING_ID [--json]
strategy-validator-paper-track assess --tracking-id TRACKING_ID [--json] \
  [--allow-promotion-despite-duplicative --duplicative-rationale "…"] [--mark-rejected]
strategy-validator-paper-track list [--json]
```

- **`enroll`** reads **`batch_summary.json`**, creates **`artifacts/paper_tracking/{tracking_id}/`**, writes **`paper_tracking_manifest.json`** (including default **`governance`**) and **`kill_rules.json`**.
- **`snapshot`** appends **`snapshots/signals/{date}.json`** and **`snapshots/outcomes/{date}.json`** (deterministic, offline).
- **`evaluate`** writes **`paper_tracking_scorecard.json`** with kill state, drift, decay warnings, and portfolio carry-forward.
- **`assess`** projects **candidate lifecycle state** from manifest + scorecard and writes **`candidate_lifecycle_assessment.json`**. Optional flags update manifest **`governance`** (DUPLICATIVE promotion override requires **`--duplicative-rationale`**; **`--mark-rejected`** sets **`lifecycle_rejected`**).
- **`list`** prints all tracking directories with derived **`lifecycle_state`** (and persisted assessment metadata).

Environment:

- **`STRATEGY_VALIDATOR_PAPER_TRACKING_ROOT`** — override artifact root (default: `{cwd}/artifacts/paper_tracking`).

Tests may set **`STRATEGY_VALIDATOR_TEST_PAPER_TRACKING_ID`**, **`STRATEGY_VALIDATOR_TEST_PAPER_CLOCK_DATE`**.

## Artifact layout

```
{paper_tracking_root}/{tracking_id}/
  paper_tracking_manifest.json          # includes portfolio carry-forward + governance
  kill_rules.json
  paper_tracking_scorecard.json          # after evaluate
  candidate_lifecycle_assessment.json     # after assess (read-plane also derives lifecycle if missing)
  snapshots/signals/YYYY-MM-DD.json
  snapshots/outcomes/YYYY-MM-DD.json
```

### Lifecycle states (evidence-only)

Contracts live in **`strategy_validator.contracts.paper_tracking`**: **`CandidateLifecycleState`**, **`CandidateLifecycleAssessment`**, **`PaperTrackingGovernance`**. States include **`RESEARCH_CANDIDATE`** (no scorecard yet) through **`PROMOTION_REVIEW_READY`**. **`PROMOTION_REVIEW_READY` is not deployment or live approval** — it is a **review queue gate** from paper evidence. Kill-rule posture maps soft triggers (e.g. drift, execution staleness) to **`KILL_CANDIDATE`** and hard triggers (loss, drawdown, operator halt) to **`KILLED_BY_RULE`**.

## Read-plane API

| Route | Description |
| --- | --- |
| `GET /ui/paper-tracking/latest` | Schema **`ui_paper_tracking/v2`**: latest bundle + **derived lifecycle** fields + optional persisted assessment artifact |
| `GET /ui/paper-tracking/{tracking_id}` | Same schema; detail for one **`tracking_id`** |

Missing artifacts → **200** with `degraded` hints (not HTTP 500).

## Frontend

- **Route:** `/paper-tracking` (terminal rail: **Paper**)
- **Read-only** — lifecycle rail (state badges, kill-rule posture, blockers), optional **promotion review** banner (with **not approval** copy), enrollment rail, kill/carry-forward notes, signal/outcome history, digests.

## Kill rules (defaults)

Default falsification rules are **heuristic** and **tunable** (see `default_kill_rules()` in `strategy_validator.contracts.paper_tracking`):

- Cumulative paper loss vs threshold  
- Max drawdown on paper equity  
- Signal drift vs baseline  
- Execution assumption staleness (days since enrollment — default threshold is conservative for CI; **tighten in production policy**)

## Operator workflow

1. Run a **gauntlet** batch; confirm **`promotion_eligible`** where intended.
2. **`paper-track enroll --batch-run ...`**
3. Schedule or run **`paper-track snapshot`** (offline deterministic demo) or integrate your own snapshot producer later.
4. **`paper-track evaluate`**; inspect **`paper_tracking_scorecard.json`**.
5. **`paper-track assess`** to persist **`candidate_lifecycle_assessment.json`** and optional governance updates.
6. Strategy Lab **Paper** page (read-plane) reflects **derived** lifecycle from manifest + scorecard; persisted assessment is shown when present.
7. **Never** treat paper evidence as live readiness or profitability proof.

## Why this is not live trading

Paper tracking **does not** send orders, **does not** connect to brokers, and **does not** mutate the ledger. It is a **falsification and evidence** layer for research operators.
