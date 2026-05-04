# Multi-strategy batch research runner

For the **full research operating workflow** (batch → paper → lifecycle → promotion packet → daily tracking → allocation) and the canonical demo script, see **[RESEARCH_OPERATING_SYSTEM.md](./RESEARCH_OPERATING_SYSTEM.md)**.

## Purpose

The strategy batch runner executes **multiple candidate strategies in parallel** under a **research / paper** posture. It writes **per-strategy evidence artifacts** and a **batch summary** to disk. It does **not** perform live trading, broker execution, or ledger commits.

**Status vocabulary:** this subsystem is a **TESTABLE_CANDIDATE** research plane addition. It does **not** change **DEPLOYMENT_APPROVED** semantics for the single-tenant API; the backend still boots without provider keys.

## Safety rules

- **Paper / research only** — batch `mode` must be `research` or `paper`. There is no live mode.
- **No ledger mutation** from the runner — `strategy_validator.research.strategy_batch_runner` does not import `ledger.writer`.
- **Optional adjudication** calls `adjudicate(..., commit=False)` via `strategy_validator.research.strategy_batch_adjudication`; authoritative promotion still requires the orchestrator + ledger path outside this demo flow.
- **Synthetic demo** data is **deterministic**, labeled `SYNTHETIC_DEMO`, sets **`may_gate_live_promotion=false`**, and surfaces **`PAPER_ONLY`** statuses.
- **Strict PIT policy** (`pit_policy: STRICT`) blocks the demo path when no real point-in-time spine data is wired (missing PIT → `BLOCKED` / `MISSING_PIT`).

## Configuration

Example batch spec:

- `configs/strategy_batches/example_batch.json`

Fields are validated by `StrategyBatchSpec` / `StrategyCandidateSpec` (`strategy_validator.contracts.strategy_batch`).

## CLI

Console script (after `pip install .`):

```bash
strategy-validator-strategy-batch-run \
  --batch configs/strategy_batches/example_batch.json \
  --output-root artifacts/strategy_runs \
  --max-workers 4 \
  --mode paper \
  --json
```

Module form:

```bash
python -m strategy_validator.cli.strategy_batch_run --batch ... 
```

Options:

| Flag | Meaning |
| --- | --- |
| `--dry-run` | Validate spec only |
| `--no-synthetic` | Disallow synthetic demo path (strategies block without real data) |
| `--fail-fast` | Stop after first failed/blocked strategy |
| `--adjudicate` | Optional `adjudicate(commit=False)` per strategy |
| `--output-root` | Override spec `output_root` |
| `--run-id` | Fixed subdirectory name under `{output_root}/{batch_id}/` (default: deterministic hash) |
| `--overwrite` | Delete an existing `{output_root}/{batch_id}/{run_id}/` tree before running (paths validated; no traversal) |
| `--worker-model` | `thread_pool` (default) or `process_pool` for CPU-heavy evaluation |
| (per candidate) `robustness_mode` | `walk_forward`, `cpcv`, or `both` (default `both`) |
| (per candidate) `oos_holdout_bars` | Optional positive int: reserve a **tail** window as out-of-sample; compares a simple Sharpe-like statistic in-sample vs OOS (`strategy_validator/research/strategy_holdout_gate.py`). |
| (per candidate) `oos_min_sharpe` | Optional float (default **-0.75**): OOS Sharpe-like floor; below it sets `oos_holdout_gate=BLOCKED` and blocks the run. |

If the run directory already exists and `--overwrite` is not set, the runner raises **`FileExistsError`** with message **`RUN_DIRECTORY_EXISTS:`** and the resolved path. With **`--json`**, the CLI prints a parseable object: `{"error":"RUN_DIRECTORY_EXISTS","ok":false,"path":"..."}` and exits **2**.

## Research gauntlet overview

Each **non-synthetic** local-bars run is intended to flow through a **governed research gauntlet** (deterministic, evidence-linked):

**Data quality → PIT snapshot → strategy metrics → performance chart artifacts → execution realism → walk-forward robustness (+ optional CPCV combinatorial layer) → parameter sensitivity → regime analysis → strategy scorecard / batch ranking → portfolio correlation summary → read-plane / Strategy Lab.**

Optional **portfolio allocation simulation** is a separate CLI (`strategy-validator-portfolio-sim`) that writes `portfolio_allocation_result.json` next to the batch summary for Strategy Lab.

Nothing in this path is **live trading**, **broker execution**, or a **profitability guarantee**. Synthetic rows remain **`PAPER_ONLY`** with **`NOT_APPLICABLE`** gates where proof is impossible.

## Artifact layout

```
{output_root}/{batch_id}/{run_id}/
  batch_manifest.json
  batch_summary.json              # includes portfolio_correlation_summary, top_candidate, promotion_blocked_counts
  batch_provider_historical_evidence.json   # present when any strategy uses provider_snapshot data_source; lists spec manifest paths + digests per strategy
  portfolio_correlation_summary.json
  strategies/{strategy_id}/
    input_manifest.json
    pit_context.json
    data_quality_result.json      # LOCAL_BAR_DATA_QUALITY_MODEL
    strategy_metrics.json
    gate_summary.json
    execution_realism_result.json
    robustness_result.json
    cpcv_result.json                # when robustness_mode includes cpcv / both
    parameter_sensitivity_result.json
    regime_analysis_result.json
    equity_curve.json
    drawdown_curve.json
    rolling_metrics.json
    fold_performance.json
    trade_markers.json            # toy path: empty markers + explanation
    strategy_scorecard.json
    data_snapshot_manifest.json   # when local_bars or provider_snapshot data_source is used
    filtered_bars.csv
    evidence_manifest.json        # digests for gauntlet layers
    adjudication_result.json      # if --adjudicate
```

Digests: component JSON bodies are SHA-256 linked (`canonical_json_sha256`) in manifests.

## Data quality gate (`LOCAL_BAR_DATA_QUALITY_MODEL`)

Evaluated on the **filtered** `StrategyBar` list. **Synthetic** → **`NOT_APPLICABLE`**. Checks include: timezone-aware timestamps, duplicate `(symbol, timestamp)`, future rows vs `as_of`, OHLC consistency, positive closes, non-negative volume, optional volume/outlier/PIT-publish warnings. **`BLOCKED`** issues block strategy **`PASSED`** status when present on real data. **`gate_summary.data_quality_gate`** mirrors the result. **`DATA_QUALITY:BLOCKED`** blocks **promotion**; **`WARNING`** does not block promotion by itself (other gates may still block).

## Performance chart artifacts

Schemas are versioned (e.g. `strategy_equity_curve/v2`): equity includes **`cumulative_return`**, **`close`**, **`exposure`** (sign proxy from toy returns); drawdown includes **`peak_equity`**; rolling metrics include **`rolling_return`**; **`trade_markers.json`** documents that discrete fills are not modeled for toy evaluators.

## Parameter sensitivity (`TOY_PARAMETER_SENSITIVITY_MODEL`)

Deterministic perturbations of supported **toy** numeric parameters; re-runs evaluator metrics on the same close series. Gates: **`STABLE`**, **`WARNING`**, **`FRAGILE`**, **`NOT_APPLICABLE`**. **`FRAGILE`** blocks **`PASSED`** and promotion (**`PARAMETER_SENSITIVITY:FRAGILE`**).

## Regime analysis (`DETERMINISTIC_REGIME_MODEL`)

Labels simple **trend × volatility** buckets from rolling price returns and summarizes toy strategy log-returns per bucket. Gates: **`PROVEN`**, **`WARNING`**, **`BLOCKED`**, **`NOT_APPLICABLE`**. **`BLOCKED`** blocks **`PASSED`** and promotion (**`REGIME_ANALYSIS:BLOCKED`**).

## Portfolio correlation (batch)

**`portfolio_correlation_summary.json`** uses aligned log-returns from **non-synthetic** strategies’ **`equity_curve.json`** files. **`NOT_APPLICABLE`** if fewer than two eligible series. High pairwise correlation (e.g. **> 0.90**) feeds **`DUPLICATIVE`** / **`WARNING`** batch posture — **not** a production diversification proof.

## Strategy scorecard and ranking

**`strategy_scorecard.json`** carries headline metrics, **all gauntlet gate statuses**, heuristic **`score`**, and **`rank_explanation`**. **`apply_batch_ranking`** orders strategies by score with **`BLOCKED`/`FAILED`** in a lower tier. **`batch_summary.json`** includes **`batch_ranking`**, **`top_candidate`** (first promoted-eligible non-blocked-tier row, if any), and **`promotion_blocked_counts`**.

## Execution realism (local bars)

The runner estimates **conservative, research-only** execution realism using **`CONSERVATIVE_LOCAL_BAR_MODEL`**. This is **not** live execution, not broker-grade, and **does not** claim profitability.

### Assumptions (in batch JSON)

Declare liquidity and cost assumptions under each strategy’s `execution_assumptions` (all of the following are **required** if any execution-realism field is present; partial keys are rejected at load time):

| Field | Meaning |
| --- | --- |
| `starting_capital` | Portfolio notional used to scale estimated daily traded notional |
| `max_participation_rate` | Cap on estimated participation vs average daily dollar volume |
| `fee_bps` / `slippage_bps` | Conservative per-unit-of-turnover costs (basis points) |
| `min_average_daily_volume` | Minimum acceptable mean `volume × close` over filtered bars |
| `allow_short` | Strategy may sell short (borrow still modeled separately) |
| `borrow_required` | If true, `borrow_liquidity_evidence_ack` must be true (operator attestation) |

Example (see `configs/strategy_batches/example_local_bars_batch.json`):

```json
"execution_assumptions": {
  "friction_bps": 5.0,
  "paper_only": true,
  "starting_capital": 1000000,
  "max_participation_rate": 0.12,
  "fee_bps": 1.0,
  "slippage_bps": 5.0,
  "min_average_daily_volume": 50000,
  "allow_short": false,
  "borrow_required": false
}
```

### Gate outcomes

`execution_realism_gate` on `gate_summary.json` / batch summary:

- **PROVEN** — Conservative checks passed (sufficient volume, participation under cap, assumptions complete, borrow rules satisfied).
- **WARNING** — Borderline participation or liquidity vs threshold; **not** treated as proven for promotion.
- **BLOCKED** — Missing volume, missing assumptions, participation too high, borrow required without ack, etc.
- **NOT_APPLICABLE** — Synthetic demo path; execution realism **cannot** be proven from toy data.

### Limitations

- Uses **mean daily dollar volume** from the filtered bar window only; no intraday depth, no venue, no borrow locate quality.
- **Promotion** remains conservative: for **non-synthetic** runs, eligibility requires **PIT verified**, **data coverage** not blocked, **`data_quality_gate != BLOCKED`**, **`execution_realism_gate == PROVEN`**, **`robustness_gate == PROVEN`**, **`parameter_sensitivity_gate != FRAGILE`**, **`regime_analysis_gate != BLOCKED`**, at least **30** bars (`STRATEGY_METRICS_LOW_SAMPLE` if fewer), and no synthetic path. Missing bar volume or unrealistic participation **blocks** the execution gate.

### Why promotion can stay false

Even with **PROVEN** execution realism, broader policy (orchestrator, ledger, deployment) may still withhold live promotion. The batch runner only produces **evidence artifacts**; it does not grant promotion authority.

## Robustness validation

The runner evaluates a **deterministic walk-forward** panel on **`filtered_bars.csv`** (real local bars only). The model label is **`WALK_FORWARD_LOCAL_BAR_MODEL`**. This is **heuristic research evidence**, **not** full combinatorial purged cross-validation (CPCV) and **not** a profitability or live-readiness claim.

### Fold metrics

For each fold, the evaluator holds out a contiguous **test** window after an expanding **train** window (no overlap, no future leakage). Per fold it records simple **train/test returns** (last close / first close − 1), **Sharpe-like** statistics from daily close returns (annualized with √252), **max drawdown** on the test closes, and whether the **test return** is positive.

### Aggregate heuristics

- **Median test return / median test Sharpe-like** — stability summaries across folds.
- **Worst fold return** — most negative test-window return across folds.
- **Positive fold ratio** — fraction of folds with a positive test return.
- **`pbo_like_score`** — **`PBO_LIKE_HEURISTIC`**: emphasizes folds where in-sample Sharpe is positive but out-of-sample Sharpe is not, plus a normalized train-vs-test Sharpe gap penalty (clipped to **[0, 1]**). This is **not** Bailey et al. PBO.
- **`dsr_like_score`** — **`DSR_LIKE_HEURISTIC`**: blends median test Sharpe, fold consistency, and sample depth (clipped to **[-1, 1]**). This is **not** the Deflated Sharpe Ratio.

### Gate status (`robustness_gate` on `gate_summary.json`)

| Status | Meaning |
| --- | --- |
| **PROVEN** | Sample supports the configured walk-forward grid; all configured thresholds passed. |
| **WARNING** | No hard blockers, but at least one threshold is **marginal** (borderline vs policy). |
| **BLOCKED** | Missing `filtered_bars.csv`, insufficient bars for the fold config, or a hard threshold failed. |
| **NOT_APPLICABLE** | **Synthetic / demo** path — robustness **cannot** be proven from toy data; digest is still written for traceability. |

### Batch JSON: `robustness_assumptions`

Optional per-strategy object. If **omitted**, defaults apply. If **present**, **all** keys must be supplied (partial objects are rejected at load time). See `configs/strategy_batches/example_local_bars_batch.json` for a **small-fixture-tuned** example (not institutional-grade thresholds).

### Sample size limitations

Short windows may fail **`INSUFFICIENT_SAMPLE_FOR_WALK_FORWARD`** even when strategy metrics run. Separately, **fewer than 30** bars in the filtered window blocks **promotion** (`STRATEGY_METRICS_LOW_SAMPLE`) even if robustness were to pass.

### How robustness affects promotion

For **non-synthetic** runs, **`promotion_eligible`** requires the **full gauntlet** listed under execution realism (data quality not **BLOCKED**, robustness **PROVEN**, parameter gate not **FRAGILE**, regime not **BLOCKED**, etc.). Robustness **`NOT_APPLICABLE`**, **`WARNING`**, and **`BLOCKED`** **withhold** promotion (reasons include `ROBUSTNESS:…`).

### Why synthetic cannot prove robustness

Synthetic prices are **deterministic demos**. **`robustness_gate`** is **`NOT_APPLICABLE`** with blockers such as **`SYNTHETIC_DEMO_NOT_ROBUSTNESS_PROOF`**; **`promotion_eligible`** stays **false** via the synthetic policy path.

## Read-plane API

| Route | Description |
| --- | --- |
| `GET /ui/strategy-batches/latest` | Latest `batch_summary.json` discovered under scan root |
| `GET /ui/strategy-batches` | Recent batch index |
| `GET /ui/strategy-batches/{run_id}` | Detail for one run |

Scan root resolution:

1. `STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT`
2. Else `${STRATEGY_VALIDATOR_ARTIFACT_ROOT}/strategy_runs`
3. Else `./artifacts/strategy_runs` relative to process cwd

Missing artifacts → **200** with `degraded` hints (not HTTP 500).

## Frontend

- **Route:** `/strategy-lab` (terminal rail: **Strategy Lab**)
- **Read-only** — no start/mutation controls; shows batch rail (including portfolio summary), leaderboard columns (rank, score, returns, gauntlet gates), gate matrix, charts, and inspector drilldowns.

## Operator workflow (research only)

1. Author or reuse a batch spec under `configs/strategy_batches/`.
2. Run **`strategy-validator-strategy-batch-run`** with **`--run-id`** and **`--overwrite`** when re-running the same logical experiment.
3. Open **Strategy Lab** to inspect gates, ranking, and correlation posture.
4. Read **`promotion_blocked_reasons`** per strategy before any orchestrator step.
5. Treat **paper** promotion as **tracking / research** only until separate governance approves further stages.
6. **Never** conflate this runner with **live** readiness; no artifact here is a profitability certificate.

## Why this is not live trading

The batch runner only materializes **research artifacts**. There is **no** order routing, **no** broker integration, and **no** ledger authority in this path.

## Why this is not a profitability guarantee

All metrics, charts, robustness scores, and rankings are **deterministic toy or heuristic** constructs on historical or synthetic inputs. They **falsify** obviously bad configurations; they **do not** certify edge or live performance.

## Concurrency

- Default `ThreadPoolExecutor` with `max_workers` capped by strategy count.
- For CPU-heavy extensions, consider `ProcessPoolExecutor` in a future tranche; keep artifact paths process-unique.

## Graduating beyond synthetic demo

1. Provide real PIT-aligned panels via existing data-spine / provider abstractions.
2. Set `pit_policy` appropriately and implement a non-demo evaluator branch in the runner (future).
3. Run orchestrator adjudication with full evidence bundles and `commit=True` only through governed operator flows — not from this batch CLI alone.

## GPU / research compute

Monte Carlo / GPU probes remain separate (`/ui/research-compute`). Batch metrics today are lightweight toy statistics suitable for CI.
