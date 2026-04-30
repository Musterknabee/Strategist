# Pilot burn-in report (local HTTP, RC `0.1.0rc1`)

**Date:** 2026-04-12  
**Scope:** Controlled liquidity probe only (no ledger writes, no Alpaca).

## Execution

| Step | Action |
|------|--------|
| Probe R1 | `python scripts/pilot_http_burnin_driver.py 60` → `pilot_burnin_round1.jsonl` (60 rounds) |
| Analyze R1 | Embedded in driver → `pilot_burnin_round1_analyze.txt` |
| Policy | No `STRATEGY_VALIDATOR_*` / YAML changes (see below) |
| Probe R2 | Second 60-round run → `pilot_burnin_round2.jsonl` |
| Analyze R2 | `pilot_burnin_round2_analyze.txt` |
| RC2 | **Not tagged** — no release-shaping code or policy change resulted from observed counts |

## Environment

- Ephemeral `127.0.0.1` HTTP server returning a LIVE-shaped JSON payload (`adv_notional`, `spread_bps`, `snapshot_time` set to current UTC per request).
- Child process env only: `STRATEGY_VALIDATOR_HTTP_MARKET_DATA_*` overrides via `scripts/pilot_http_burnin_driver.py` (see script for exact template URL).

## Observed aggregates (both rounds)

- **Rounds:** 60 each; **provider_status:** 100% `SUCCESS`.
- **failure_domain / failure_code:** all `NONE` (no typed vendor failures).
- **rate_limit_proxy_rounds:** 0; **auth_domain_rounds:** 0.
- **stale_or_old_snapshot_rounds:** 0 (per analyzer thresholds on this fixture).
- **snapshot_age_s:** max about **0.66 s** (R1/R2) — echo server returns `snapshot_time` at request time (sub-second skew vs single `evaluated_at_utc` reused across rounds in the probe loop).
- **latency_ms p95:** ~23 ms (R1), similar R2 — loopback only; **not** used to change production timeouts (not WAN-comparable).

## Analyzer suggestions

Both runs printed only the default line: *no strong aggregate signals — keep policy; extend pilot sample size.*

## Policy / env changes applied

**None.** Nothing in the aggregate output met the observation-only gates in `pilot_aggregate.suggest_env_from_summary` (rate-limit, stale, auth, 5xx, high p95 in a comparable setting).

## Follow-ups (outside this burn-in)

- Repeat with **Alpaca or staging HTTP** when credentials are available; re-run `pilot analyze` and apply only lines that cross the documented count thresholds.

## Tooling fix

- `strategy_validator.cli.pilot`: removed invalid `argparse` `ge`/`le` kwargs; rounds validated in `run_probe` (1..500).
- `scripts/pilot_http_burnin_driver.py`: echo liquidity uses **current UTC** `snapshot_time` so snapshot age stays near-zero for this fixture.

---

## Follow-up burn-in (Alpaca-only, three passes, agent host 2026-04-12)

**Host caveat:** These commands were executed in the **Cursor agent environment**, which does **not** load operator Alpaca secrets. Every round failed fast with `ALPACA_CREDENTIALS_MISSING` / `MISSING_CREDENTIALS`, then the provider circuit latched **OPEN**. Aggregates below describe **that** failure mode only. They are **not** comparable to a credentialed laptop run for freshness law, off-hours law, or SPY vs QQQ vendor parity. **Re-run the same three commands on a machine where `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` (or your project’s configured key env names) are set.**

### Per-run record (requested fields)

| Run | Command | Rounds | Symbol | UTC window (first/last row `evaluated_at_utc`) | Success (`provider_status` = SUCCESS) | Stale / freshness | Fallback | Timeout (proxy) | Retry (sum `retry_count`) | Circuit (`CIRCUIT_OPEN` / OPEN) | Rate-limit proxy | Auth / creds |
|-----|---------|--------|--------|---------------------------------------------------|----------------------------------------|---------------------|----------|-------------------|---------------------------|----------------------------------|-------------------|--------------|
| Long | `python scripts/pilot_followup_burnin_driver.py long 180` | 180 | SPY (default) | `2026-04-12T14:34:18.195974+00:00` … `2026-04-12T14:34:18.212184+00:00` | **0 / 180** | `effective_freshness_status`: **MISSING ×180**; analyzer `stale_or_old_snapshot_rounds`: **0** (no LIVE age—no snapshot) | **0** | **0** | **0** (all rows `retry_count`: 0) | **178** rounds `CIRCUIT_OPEN` + **2** `ERROR` (after trips) | **0** | **2** rows `AUTH` / `MISSING_CREDENTIALS`; `auth_domain_rounds` **4** (domain + vendor-event double count in summary) |
| Off-hours | `python scripts/pilot_followup_burnin_driver.py off-hours 60` | 60 | SPY (default) | Same wall-clock block as batch (~`14:34:28Z` banner); rows sub-second span | **0 / 60** | **MISSING ×60**; stale proxy **0** | **0** | **0** | **0** | **58** `CIRCUIT_OPEN` + **2** `ERROR` | **0** | Same AUTH pattern |
| Second symbol | `python scripts/pilot_followup_burnin_driver.py symbol QQQ 60` | 60 | **QQQ** | `2026-04-12T14:34:36.960715+00:00` … (same second) | **0 / 60** | **MISSING ×60**; stale proxy **0** | **0** | **0** | **0** | **58** + **2** | **0** | Same AUTH pattern |

Artifacts (gitignored where matched by `pilot_*` patterns): `pilot_followup_alpaca_long.jsonl`, `pilot_followup_alpaca_long_analyze.txt`, `pilot_followup_alpaca_off_hours.*`, `pilot_followup_alpaca_sym_QQQ.*`.

### Comparison (what you asked for, **given credential absence**)

- **Success rate:** **0%** all three; not a stability signal—credentials missing.
- **Stale counts:** Analyzer shows **no** `STALE` / `stale_or_old_snapshot` inflation; freshness is **MISSING** because no snapshot was returned.
- **Fallback counts:** **0** all three (`fallback_applied_rounds`: 0).
- **Timeout / retry / circuit:** **Timeouts:** 0 (proxy). **Retries:** 0 every round. **Circuit:** Dominant status after the first auth failures—expected for this provider when lookups fail without recovery.
- **Auth / rate-limit:** **AUTH / MISSING_CREDENTIALS** on the first failing lookups; **no** rate-limit proxy hits.
- **SPY vs QQQ:** **No symbol-specific vendor difference** observable—both hit the same credential error before any instrument-specific Alpaca path matters.
- **Off-hours vs “regular” on this host:** Both are the same **non-session** outcome; the `off-hours` driver only printed `us_equities_regular_session_open=False` at start—**no** comparative RTH data exists in these files.

### What this pass was trying to prove (operator intent vs this host)

| Goal | Verdict on **this** artifact set |
|------|----------------------------------|
| Long run: stable success, no creeping timeout/circuit, no fallback growth | **Not demonstrated**—0 successes; circuit opens immediately after auth failure. |
| Off-hours: freshness law, no false fresh LIVE, no stale spikes forcing thresholds | **Not testable**—no LIVE snapshots. |
| Second symbol: mapping, not SPY-only luck, stable telemetry | **Not testable**—same credential failure for QQQ. |

### RC decision rule (applied here)

- No evidence here that **freshness thresholds**, **provider taxonomy**, **fallback policy**, **session law**, **symbol handling**, or **retry/circuit leniency** need a **code or RC tag** change—because the run never reached lawful LIVE liquidity.
- **RC2** is **not** justified by these aggregates (they do not show a product defect or interface gap).
- A **credentialed** re-run is still required before claiming the stronger statement that the **pilot objectives** (freshness/vendor/symbol/off-hours) are satisfied.

### Policy / env changes applied (this host)

**None** (no `STRATEGY_VALIDATOR_*` edits from these files). Analyzer suggested fixing credentials—not threshold tuning.

### One-sentence closeout

**RC1 stands; no changes justified** *to thresholds, fallback policy, or RC2 tagging based solely on this agent-host follow-up (missing Alpaca credentials; re-run the same three commands where keys are present to judge freshness law and symbol parity).*

### Follow-up rerun table (agent host, 2026-04-13)

This section is an explicit second table appended to keep the decision history continuous in one document.

| Run | Command | Rounds | Symbol | Success | Stale | Error/Circuit | Fallback | Timeout/Retry | Auth/Rate-limit | Notes |
|-----|---------|--------|--------|---------|-------|---------------|----------|---------------|-----------------|-------|
| Long rerun | `python scripts/pilot_followup_burnin_driver.py long 180` | 180 | SPY | 0 | 0 (`MISSING` freshness all rounds) | `ERROR`: 2, `CIRCUIT_OPEN`: 178 | 0 | `timeout_signal_rounds`: 0, retries all 0 | AUTH: present (`MISSING_CREDENTIALS`), rate-limit: 0 | Same credential-missing pattern; not a valid vendor/freshness burn-in |
| Off-hours rerun | `python scripts/pilot_followup_burnin_driver.py off-hours 60` | 60 | SPY | 0 | 0 (`MISSING` freshness all rounds) | `ERROR`: 2, `CIRCUIT_OPEN`: 58 | 0 | `timeout_signal_rounds`: 0, retries all 0 | AUTH: present, rate-limit: 0 | Off-hours flag printed as outside RTH; still no LIVE snapshots |
| Second-symbol rerun | `python scripts/pilot_followup_burnin_driver.py symbol QQQ 60` | 60 | QQQ | 0 | 0 (`MISSING` freshness all rounds) | `ERROR`: 2, `CIRCUIT_OPEN`: 58 | 0 | `timeout_signal_rounds`: 0, retries all 0 | AUTH: present, rate-limit: 0 | No SPY/QQQ difference is measurable before auth succeeds |

Result: this rerun still does not satisfy the "machine with working Alpaca keys" requirement; the same three commands must be executed in a credentialed environment for the intended RC evidence.

## Milestone tag

Credentialed-provider caveat: this milestone confirms the local/staging-shaped pilot burn-in package and controlled-rollout handoff only. The Alpaca follow-up tables above remain credential-missing evidence and must not be used as proof of LIVE freshness, off-hours, or SPY/QQQ provider parity.

- Milestone: `PILOT_BURNIN_COMPLETE`
- Archive: `docs/artifacts/pilot_burnin_complete_20260413T080723Z`
- Fingerprint: `docs/artifacts/pilot_burnin_complete_20260413T080723Z/RUN_FINGERPRINT.json`
- Rollout status: moved from engineering validation to controlled operational rollout (canary + append-only evidence updates in this file).

## Controlled rollout bundle

- Bundle artifact: `docs/artifacts/controlled_rollout_bundle.json`
- Fingerprint reference: `docs/artifacts/keyed_host_fingerprint.json`
- Burn-in references in bundle: `pilot_followup_alpaca_long_analyze.txt`, `pilot_followup_alpaca_off_hours_analyze.txt`, `pilot_followup_alpaca_sym_QQQ_analyze.txt`
- Signoff fields remain null until operator approval is recorded.
