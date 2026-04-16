# Operator runbook

This document describes **runtime states**, **common blockers**, and **lawful fallbacks** for the strategy validator. It is not a substitute for reading the constitutional tests and contracts.

Pilot / RC procedures (interface freeze, probe, analyze): see `docs/PILOT_READINESS.md`.

## Readiness states

| Status | Meaning | Adjudication |
|--------|---------|--------------|
| `READY` | Ledger path, schema, and production source policy checks passed. | Allowed (subject to per-request gates). |
| `DEGRADED` | Non-fatal check inconsistencies (rare with current gates). | Disallowed when `adjudication_allowed` is false. |
| `BLOCKED` | One or more `ReadinessBlocker` entries — fail-closed. | Disallowed; `adjudicate` raises `ConstitutionalViolation`. |

## Frequent blockers and remediation

- **`UNSAFE_LEDGER_PATH` / `DEFAULT_LEDGER_PATH_FORBIDDEN`**: set `STRATEGY_VALIDATOR_LEDGER_DB_PATH` to an **absolute** non-default SQLite path.
- **`INCOMPATIBLE_SCHEMA`**: run migrations so ledger schema version ≥ expected version.
- **`INSECURE_SOURCE_POLICY`**: in `PRODUCTION`, `allow_provisional_market_data` must be `False`.
- **`CALIBRATION_ARTIFACT_MISSING` / `CALIBRATION_ARTIFACT_INVALID`**: when `capacity_impact_model=CALIBRATED`, provide a valid `CalibrationArtifactV1` JSON file via `STRATEGY_VALIDATOR_CALIBRATION_ARTIFACT_PATH`, or switch to `HEURISTIC`.

## Market data: degraded vs blocked

- **Stale LIVE liquidity** with `allow_market_data_fallback=False` and strict production: execution realism fails; promotion is restricted (typically `REJECTED`). This is **blocked** for promotion-grade outcomes, not a silent degrade.
- **Explicit SNAPSHOT fallback** is permitted only when **both** `allow_market_data_fallback` and `allow_snapshot_market_data` are true. Provenance must record `fallback_applied` and `fallback_reason`; telemetry mirrors these fields.
- **`PROVISIONAL`**: never treated as LIVE/SNAPSHOT. In strict production it is a **hard blocker** for promotable-class outcomes.

## Vendor outage circuit policy (optional)

`STRATEGY_VALIDATOR_MARKET_DATA_VENDOR_OUTAGE_CIRCUIT_POLICY` controls how HTTP **5xx-class** Alpaca/HTTP-JSON errors advance the provider circuit breaker:

- `STANDARD` (default): every failed lookup increments toward `circuit_breaker_threshold`.
- `LENIENT_TRANSIENT_5XX`: 5xx-shaped error strings **do not** increment the counter (useful when vendors flap during outages; still surfaces `ERROR` provenance on each call).

Wire feeds with `provider_resilience_from_runtime_policy(load_config().runtime_policy)` so retries/circuit fields stay aligned with env-driven policy.

## LIVE freshness and US regular session (optional)

When `STRATEGY_VALIDATOR_LIVE_FRESHNESS_MARKET_HOURS_PROFILE=US_EQUITIES_RTH`, LIVE snapshot age is compared against `STRATEGY_VALIDATOR_LIVE_MARKET_DATA_FRESHNESS_THRESHOLD_SECONDS` **during** NYSE regular hours (weekday 09:30–16:00 `America/New_York`), and against `STRATEGY_VALIDATOR_LIVE_FRESHNESS_OFF_HOURS_THRESHOLD_SECONDS` **outside** that window. This is a **calendar simplification** (no exchange holidays); for holiday correctness use SNAPSHOT feeds or upstream calendar-aware data.

## Vendor failure taxonomy

`MarketDataProvenance` carries both human `provider_errors` strings and typed `vendor_failure_events` (`domain`, `code`, `feed_kind`, `provider_id`) for aggregation in logs or metrics. Primary liquidity/borrow paths use `liquidity` / `borrow`; configured fallback feeds use `fallback_liquidity` / `fallback_borrow`.

Alpaca and HTTP JSON providers emit **stable** `RuntimeError` tokens (for example `ALPACA_HTTP_401`, `ALPACA_HTTP_403`, `ALPACA_HTTP_429|RETRY_AFTER=…`, `ALPACA_LIQUIDITY_MISSING_QUOTES`, `HTTP_JSON_LIQUIDITY_FIELDS_INVALID`) so classifiers and dashboards do not depend on parsing stack traces.

When US RTH freshness law is enabled, `liquidity_market_hours_law` / `borrow_market_hours_law` on provenance record the session context used for LIVE age thresholds (`DISABLED` | `US_RTH_OPEN` | `US_RTH_CLOSED`).

## Calibration governance (production CALIBRATED)

Beyond JSON schema validation, readiness can **reject** artifacts using env-tunable gates:

- `STRATEGY_VALIDATOR_CALIBRATION_MINIMUM_VALIDATION_SCORE` — requires `validation_quality_score` on the artifact and rejects when below threshold.
- `STRATEGY_VALIDATOR_CALIBRATION_REJECT_FLAT_CURVE_SPREAD_BPS_BELOW` — rejects empirical curves whose `max(impact_bps)-min(impact_bps)` is below the floor.
- `STRATEGY_VALIDATOR_CALIBRATION_REQUIRE_TRAINING_RUN_ID` — requires `training_run_id`.
- `STRATEGY_VALIDATOR_CALIBRATION_REQUIRE_EMPIRICAL_CURVE_IN_PRODUCTION` — disallows multiplier-only artifacts in production CALIBRATED mode.

Failures surface as readiness blocker `CALIBRATION_GOVERNANCE_REJECTED`. Use `python -m strategy_validator.cli.calibration --artifact … --check-governance` in CI before publishing an artifact.

## Telemetry export failures

Sinks configured via `STRATEGY_VALIDATOR_TELEMETRY_JSONL_PATH` / `STRATEGY_VALIDATOR_TELEMETRY_HTTP_URL` are **best-effort**. Failures are logged and **must not** change adjudication results.

### HTTP sink operations

- **Retries**: `STRATEGY_VALIDATOR_TELEMETRY_HTTP_MAX_RETRIES` (default `3`) with exponential backoff from `STRATEGY_VALIDATOR_TELEMETRY_HTTP_BACKOFF_START_MS` (default `100`).
- **Bearer auth**: set `STRATEGY_VALIDATOR_TELEMETRY_HTTP_BEARER_TOKEN_ENV` to the **name** of an environment variable whose value is the raw bearer token (value never appears in config files).
- **Static header**: optional `STRATEGY_VALIDATOR_TELEMETRY_HTTP_AUTH_HEADER` as `Header-Name: value` for collectors that require a non-bearer scheme.

## Runtime metrics (Prometheus-style)

After each adjudication, a small gauge bundle may be written when configured:

- **Textfile collector**: `STRATEGY_VALIDATOR_METRICS_TEXTFILE_PATH` (append-only exposition text).
- **Pushgateway**: `STRATEGY_VALIDATOR_METRICS_PUSHGATEWAY_URL` with optional `STRATEGY_VALIDATOR_METRICS_PUSH_JOB` (default `strategy_validator`).

Failures are logged only; they do not affect promotion outcomes.

The integration test `tests/integration/test_telemetry_metrics_file_e2e.py` exercises **JSONL telemetry** plus **Prometheus textfile** emission in one run (stdlib file I/O only — no external daemon required).

## Alpaca Market Data (live liquidity + optional borrow/locate)

Enable with `STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED=True` and standard `APCA_API_KEY_ID` / `APCA_API_SECRET_KEY` (or override env names in YAML under `market_data_alpaca_connector`).

- **Liquidity**: Alpaca Market Data **stock snapshot** (`/v2/stocks/{symbol}/snapshot`).
- **Borrow / locate** (opt-in): set `STRATEGY_VALIDATOR_ALPACA_ENABLE_BORROW_FROM_TRADING_API=True`. The provider then calls the Trading API **asset** endpoint (`GET /v2/assets/{symbol}`) using `trading_base_url` (paper: `https://paper-api.alpaca.markets`, live: `https://api.alpaca.markets`).
  - `borrow_available` ← `shortable`; `locate_required` ← not `easy_to_borrow` (HTB).
  - **Borrow fee**: the asset JSON does not include an annualized borrow rate. `etb_borrow_cost_bps` / `htb_borrow_cost_bps` are **explicit operator tier assumptions** (defaults are starting points only—tune per desk policy).

## Empirical calibration curve

When `empirical_participation_curve` is present in the calibration JSON artifact (≥3 points, strictly increasing `participation_rate`), adjudication uses **piecewise-linear** impact in bps from that curve. Invalid curves fail readiness in `PRODUCTION` + `CALIBRATED` mode.

### Validate an artifact locally

`python -m strategy_validator.cli.calibration --artifact /path/to/calibration_v1.json`

Optional sampling against the curve:

`python -m strategy_validator.cli.calibration --artifact /path/to/calibration_v1.json --participation 0.02 --participation 0.10 --json`

## Startup self-check

Run:

`python -m strategy_validator.cli.startup_check`

JSON bundle (for init containers / agents):

`python -m strategy_validator.cli.startup_check --json`

Exit code `0` only when readiness is `READY` and the HTTP JSON connector (if enabled) passes static validation.

## Controlled rollout operations (RC1 delta)

Use `strategy_validator.cli.rollout_ops` for typed, auditable rollout artifacts:

1. **Keyed-host fingerprint** (secret-safe, hash/presence only):

`python -m strategy_validator.cli.rollout_ops fingerprint --host-kind KEYED_OPERATOR_HOST --host-label ops-paper-1 --output docs/artifacts/keyed_host_fingerprint.json`

2. **Rollout bundle** (frozen release/config/policy + scope):

`python -m strategy_validator.cli.rollout_ops bundle --fingerprint docs/artifacts/keyed_host_fingerprint.json --artifacts pilot_burnin_round_http_staging_analyze.txt pilot_burnin_round_alpaca_analyze.txt pilot_followup_alpaca_long_analyze.txt pilot_followup_alpaca_off_hours_analyze.txt pilot_followup_alpaca_sym_QQQ_analyze.txt --environment paper --provider alpaca_data_v2 --symbols SPY,QQQ --allowed-actions observe,archive,recommend --output docs/artifacts/controlled_rollout_bundle.json`

3. **Daily checklist** (machine/human operational gate):

`python -m strategy_validator.cli.rollout_ops daily-checklist --analyze pilot_followup_alpaca_long_analyze.txt pilot_followup_alpaca_off_hours_analyze.txt pilot_followup_alpaca_sym_QQQ_analyze.txt --use-live-startup --output docs/artifacts/daily_checklist.json`

4. **Release decision review** (rule-based):

`python -m strategy_validator.cli.rollout_ops review docs/artifacts/daily_checklist.json --output docs/artifacts/release_decision.json`

5. **Canonical closure snapshot** (digest-anchored manifest + optional DSSE signature):

Generate a local Ed25519 keypair once for operator-side signing:

`python -m strategy_validator.cli.rollout_ops snapshot-keypair --private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem`

Build the snapshot from a canonical closure directory (use `--allow-incomplete` only for forensic inspection of stale or partial evidence chains):

`python -m strategy_validator.cli.rollout_ops closure-snapshot --closure-dir docs/artifacts/release_closure_2026-04-13 --signing-private-key .keys/closure_snapshot_private.pem --output docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --dsse-output docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.dsse.json`

Verify digests and the DSSE envelope before treating the closure package as canonical:

`python -m strategy_validator.cli.rollout_ops verify-closure-snapshot docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --dsse docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.dsse.json --public-key .keys/closure_snapshot_public.pem`

Derive the machine signoff package from the closure snapshot instead of hand-editing final signoff docs:

`python -m strategy_validator.cli.rollout_ops closure-attestation docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --dsse docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.dsse.json --public-key .keys/closure_snapshot_public.pem --verification-output docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.verification.json --output docs/artifacts/release_closure_2026-04-13/ATTESTED_RELEASE_DECISION.json --signoff-output docs/artifacts/release_closure_2026-04-13/FINAL_RELEASE_SIGNOFF.md --reconciliation-output docs/artifacts/release_closure_2026-04-13/DECISION_RECONCILIATION.md`

6. **Governed exception workflow** (environmental nonconformance only, signed and time-bounded):

Issue a governed exception memo only after the closure snapshot verifies and the machine attestation marks the closure as governed-exception eligible:

`python -m strategy_validator.cli.rollout_ops governed-exception --snapshot docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --verification docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.verification.json --exception-code freshness_nonconformance_without_runtime_failure --requested-by operator.jpk --approved-by release.authority --valid-until 2026-04-14T10:00:00Z --rationale "Paper-market freshness remained environmentally degraded while runtime health stayed clean." --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION_MEMO.json --dsse-output docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION_MEMO.dsse.json --verification-output docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION.verification.json --markdown-output docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION_MEMO.md`

Re-derive the closure attestation with the verified exception memo to preserve the current baseline lawfully:

`python -m strategy_validator.cli.rollout_ops closure-attestation docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --dsse docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.dsse.json --public-key .keys/closure_snapshot_public.pem --governed-exception docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION_MEMO.json --governed-exception-dsse docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION_MEMO.dsse.json --governed-exception-public-key .keys/closure_snapshot_public.pem --verification-output docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.verification.json --governed-exception-verification-output docs/artifacts/release_closure_2026-04-13/GOVERNED_EXCEPTION.verification.json --output docs/artifacts/release_closure_2026-04-13/ATTESTED_RELEASE_DECISION.json --signoff-output docs/artifacts/release_closure_2026-04-13/FINAL_RELEASE_SIGNOFF.md --reconciliation-output docs/artifacts/release_closure_2026-04-13/DECISION_RECONCILIATION.md`

Bundle creation now fails closed if the referenced burn-in artifacts do not exist. The closure snapshot builder also fails closed unless `--allow-incomplete` is explicitly supplied. Governed exceptions do not waive runtime failures, evidence-integrity failures, or production validation, and they expire automatically.

### Release taxonomy

`RuntimeEvidenceReview` and closure attestation now distinguish between:

- `RUNTIME_FAILURE` — startup/readiness, auth, or circuit-recovery blockers requiring remediation.
- `DATA_QUALITY_DEGRADATION` — measurable signal degradation that does not yet imply total runtime failure.
- `ENVIRONMENTAL_NONCONFORMANCE` — scoped environment mismatch (for example paper-data freshness behavior) that may be governed-exception eligible.
- `EVIDENCE_INTEGRITY_FAILURE` — missing, unsigned, incomplete, or digest-mismatched closure evidence.
- `POLICY_MISMATCH` — thresholds or release laws now disagree with the observed environment and need explicit RC2 discussion.
- `WITHIN_BOUNDS` — verified evidence remains within keep-current-release limits.

Operators must not silently reinterpret `CANDIDATE_RC2`, `BLOCK_AND_INVESTIGATE`, or evidence-integrity findings as clean release closure. Final signoff docs must be re-derived from the latest closure snapshot and verification artifacts.

### Release/rollback criteria source

Rule thresholds are versioned in:

`strategy_validator/policies/controlled_rollout_rules.json`

Decision outputs are:

- `KEEP_CURRENT_RELEASE`
- `CANDIDATE_RC2`
- `BLOCK_AND_INVESTIGATE`
- `ROLLBACK_RECOMMENDED`

These are operator recommendations, not autonomous promotion/rollback actions.


## Oracle advisory mode (read-only intelligence layer)

Use the deterministic advisory oracle to synthesize macro, semantic, microstructure, and strategy-health inputs into a morning state report. This layer is **advisory only** and must not autonomously route capital or mutate production state.

Build an advisory report from a frozen sensor payload:

`python -m strategy_validator.cli.rollout_ops oracle-advisory docs/artifacts/oracle_input.json --output docs/artifacts/ORACLE_MORNING_ATTESTATION.json --markdown-output docs/artifacts/ORACLE_MORNING_ATTESTATION.md`

Freeze that advisory output into signed oracle evidence, and optionally link it to a verified closure snapshot so the reasoning layer becomes replayable governance evidence:

`python -m strategy_validator.cli.rollout_ops oracle-evidence docs/artifacts/oracle_input.json --closure-snapshot docs/artifacts/release_closure_2026-04-13/CLOSURE_SNAPSHOT.json --signing-private-key .keys/closure_snapshot_private.pem --attestation-output docs/artifacts/ORACLE_MORNING_ATTESTATION.json --markdown-output docs/artifacts/ORACLE_MORNING_ATTESTATION.md --output docs/artifacts/ORACLE_EVIDENCE.json --dsse-output docs/artifacts/ORACLE_EVIDENCE.dsse.json`

Verify the oracle evidence package before relying on it for operator review, replay, or later release forensics:

`python -m strategy_validator.cli.rollout_ops verify-oracle-evidence docs/artifacts/ORACLE_EVIDENCE.json --dsse docs/artifacts/ORACLE_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/ORACLE_EVIDENCE.verification.json`

Compare two verified oracle evidence manifests to derive a machine-readable state transition report:

`python -m strategy_validator.cli.rollout_ops oracle-transition docs/artifacts/oracle/2026-04-13/ORACLE_EVIDENCE.json docs/artifacts/oracle/2026-04-14/ORACLE_EVIDENCE.json --repo-root . --previous-dsse docs/artifacts/oracle/2026-04-13/ORACLE_EVIDENCE.dsse.json --current-dsse docs/artifacts/oracle/2026-04-14/ORACLE_EVIDENCE.dsse.json --previous-public-key .keys/closure_snapshot_public.pem --current-public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_STATE_TRANSITION_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_STATE_TRANSITION_REPORT.md`

The oracle transition report remains **advisory only**. Treat `EVIDENCE_GAP` as a repair signal for missing or unverified oracle evidence before interpreting any regime or strategy drift.

Freeze that transition report into signed transition evidence so it can be archived, replayed, and appended into the oracle memory lane:

`python -m strategy_validator.cli.rollout_ops oracle-transition-evidence docs/artifacts/oracle/2026-04-13/ORACLE_EVIDENCE.json docs/artifacts/oracle/2026-04-14/ORACLE_EVIDENCE.json --repo-root . --previous-dsse docs/artifacts/oracle/2026-04-13/ORACLE_EVIDENCE.dsse.json --current-dsse docs/artifacts/oracle/2026-04-14/ORACLE_EVIDENCE.dsse.json --previous-public-key .keys/closure_snapshot_public.pem --current-public-key .keys/closure_snapshot_public.pem --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_STATE_TRANSITION_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_STATE_TRANSITION_REPORT.md --output docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.verification.json`

Append verified transition evidence into the append-only JSONL memory lane and emit a machine-readable lane entry:

`python -m strategy_validator.cli.rollout_ops oracle-memory-append docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_MEMORY_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_TRANSITION_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_MEMORY_LANE_ENTRY.json`

Summarize the memory lane for multi-day drift review without granting execution authority:

`python -m strategy_validator.cli.rollout_ops oracle-memory-summary --lane-path docs/artifacts/oracle/ORACLE_MEMORY_LANE.jsonl --output docs/artifacts/oracle/ORACLE_MEMORY_LANE_SUMMARY.json --markdown-output docs/artifacts/oracle/ORACLE_MEMORY_LANE_SUMMARY.md`

Review the rolling memory window to derive an explicit multi-day advisory posture from repeated evidence gaps, epistemic escalation, defensive drift, and strategy confidence decay:

`python -m strategy_validator.cli.rollout_ops oracle-memory-review --lane-path docs/artifacts/oracle/ORACLE_MEMORY_LANE.jsonl --repo-root . --window-size 7 --output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_REPORT.md`

Freeze that rolling memory judgment into signed review evidence so it becomes replayable doctrine evidence rather than a disposable report:

`python -m strategy_validator.cli.rollout_ops oracle-memory-review-evidence --lane-path docs/artifacts/oracle/ORACLE_MEMORY_LANE.jsonl --repo-root . --window-size 7 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_REPORT.md --output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json`

Append verified review evidence into the higher-level review lane so weekly doctrine summaries are built from signed, append-only review history:

`python -m strategy_validator.cli.rollout_ops oracle-review-lane-append docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_REVIEW_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_MEMORY_REVIEW_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_REVIEW_LANE_ENTRY.json`

Generate a weekly Oracle Digest from the append-only review lane to classify persistent doctrine posture across signed review history:

`python -m strategy_validator.cli.rollout_ops oracle-weekly-digest --lane-path docs/artifacts/oracle/ORACLE_REVIEW_LANE.jsonl --window-size 7 --output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST.md`

Freeze that weekly digest into signed digest evidence so doctrine posture becomes replayable and tamper-evident:

`python -m strategy_validator.cli.rollout_ops oracle-weekly-digest-evidence --lane-path docs/artifacts/oracle/ORACLE_REVIEW_LANE.jsonl --repo-root . --window-size 7 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST.md --output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_WEEKLY_DIGEST_EVIDENCE.verification.json`

Compare two verified weekly digest evidence manifests to derive a doctrine drift report that classifies week-over-week escalation, relief, recurring repair pressure, recurring retrain pressure, or doctrine evidence gaps:

`python -m strategy_validator.cli.rollout_ops oracle-doctrine-drift docs/artifacts/oracle/week1/ORACLE_WEEKLY_DIGEST_EVIDENCE.json docs/artifacts/oracle/week2/ORACLE_WEEKLY_DIGEST_EVIDENCE.json --repo-root . --previous-dsse docs/artifacts/oracle/week1/ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json --current-dsse docs/artifacts/oracle/week2/ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json --previous-public-key .keys/closure_snapshot_public.pem --current-public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_REPORT.md`

Freeze that doctrine drift into signed evidence so week-over-week doctrine movement becomes tamper-evident and append-only doctrine memory can be built from verified comparisons:

`python -m strategy_validator.cli.rollout_ops oracle-doctrine-drift-evidence docs/artifacts/oracle/week1/ORACLE_WEEKLY_DIGEST_EVIDENCE.json docs/artifacts/oracle/week2/ORACLE_WEEKLY_DIGEST_EVIDENCE.json --repo-root . --previous-dsse docs/artifacts/oracle/week1/ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json --current-dsse docs/artifacts/oracle/week2/ORACLE_WEEKLY_DIGEST_EVIDENCE.dsse.json --previous-public-key .keys/closure_snapshot_public.pem --current-public-key .keys/closure_snapshot_public.pem --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_REPORT.md --output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json`

Append verified doctrine-drift evidence into the doctrine lane so longer-horizon governance memory stays replayable and tamper-evident:

`python -m strategy_validator.cli.rollout_ops oracle-doctrine-lane-append docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_DOCTRINE_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_DOCTRINE_DRIFT_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_DOCTRINE_LANE_ENTRY.json`

Generate a monthly digest from the append-only doctrine lane to classify persisted doctrine memory across multiple verified weekly windows:

`python -m strategy_validator.cli.rollout_ops oracle-monthly-digest --lane-path docs/artifacts/oracle/ORACLE_DOCTRINE_LANE.jsonl --window-size 4 --output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST.md`

`python -m strategy_validator.cli.rollout_ops oracle-monthly-digest-evidence --lane-path docs/artifacts/oracle/ORACLE_DOCTRINE_LANE.jsonl --repo-root . --window-size 4 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST.md --output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops verify-oracle-monthly-digest-evidence docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops oracle-monthly-lane-append docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_MONTHLY_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_MONTHLY_DIGEST_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_MONTHLY_LANE_ENTRY.json`

`python -m strategy_validator.cli.rollout_ops oracle-quarterly-review --lane-path docs/artifacts/oracle/ORACLE_MONTHLY_LANE.jsonl --window-size 3 --output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW.json --markdown-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW.md`

`python -m strategy_validator.cli.rollout_ops oracle-quarterly-review-evidence --lane-path docs/artifacts/oracle/ORACLE_MONTHLY_LANE.jsonl --repo-root . --window-size 3 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW.json --markdown-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW.md --output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops verify-oracle-quarterly-review-evidence docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops oracle-quarterly-lane-append docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_QUARTERLY_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_QUARTERLY_REVIEW_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_QUARTERLY_LANE_ENTRY.json`

`python -m strategy_validator.cli.rollout_ops oracle-semiannual-audit --lane-path docs/artifacts/oracle/ORACLE_QUARTERLY_LANE.jsonl --window-size 2 --output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT.json --markdown-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT.md`

`python -m strategy_validator.cli.rollout_ops oracle-semiannual-audit-evidence --lane-path docs/artifacts/oracle/ORACLE_QUARTERLY_LANE.jsonl --repo-root . --window-size 2 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT.json --markdown-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT.md --output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops verify-oracle-semiannual-audit-evidence docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops oracle-semiannual-lane-append docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_SEMIANNUAL_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_SEMIANNUAL_AUDIT_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_SEMIANNUAL_LANE_ENTRY.json`

`python -m strategy_validator.cli.rollout_ops oracle-annual-review --lane-path docs/artifacts/oracle/ORACLE_SEMIANNUAL_LANE.jsonl --window-size 2 --output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW.json --markdown-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW.md`

Treat `DOCTRINE_EVIDENCE_GAP` as a repair-first signal for missing or unverified weekly digest artifacts before relying on any doctrine comparison. Treat `RECURRING_REPAIR` and `RECURRING_RETRAIN` as persisted weekly governance pressure, not one-off narrative interpretation. Treat `DOCTRINE_REPAIR_PERSISTENT`, `DOCTRINE_RETRAIN_PERSISTENT`, and `DOCTRINE_DEFENSIVE_PERSISTENT` as longer-horizon monthly doctrine memory, not transient commentary. Treat `QUARTERLY_EVIDENCE_GAP` as a repair-first signal for missing or unverified monthly digest artifacts before relying on semiannual audit posture. Treat `QUARTERLY_REPAIR_STRUCTURAL`, `QUARTERLY_RETRAIN_STRUCTURAL`, and `QUARTERLY_DEFENSIVE_STRUCTURAL` as structural quarterly doctrine, not temporary narrative noise. Treat `SEMIANNUAL_EVIDENCE_GAP` as a repair-first signal for missing or unverified quarterly audit evidence before relying on annual doctrine review. Treat `SEMIANNUAL_REPAIR_STRUCTURAL`, `SEMIANNUAL_RETRAIN_STRUCTURAL`, and `SEMIANNUAL_DEFENSIVE_STRUCTURAL` as sustained semiannual doctrine, not temporary narrative relief.

The memory review remains **advisory only**. Treat `REPAIR_FIRST` as a mandatory evidence-repair posture, `DEFENSIVE_RESEARCH_POSTURE` as a signal to slow high-conviction interpretation under epistemic stress, and `STRATEGY_RETRAIN_REVIEW` as a strategy-health escalation for repeated posterior-confidence decay. Preserve both JSONL lanes as append-only history; do not rewrite prior entries.

The advisory report currently emits:

- regime probabilities across `RISK_ON_LOW_VOL`, `TRANSITION`, `RISK_OFF_HIGH_VOL`, and `LIQUIDITY_STRESS`
- strategy-health advisories (`MAINTAIN`, `CANARY`, `HIBERNATE`) derived from prior edge confidence, CPCV lower bound, live Sharpe, and drawdown
- an epistemic uncertainty assessment (`NOMINAL`, `ELEVATED`, `UNKNOWN_UNKNOWNS`)
- a global advisory action (`OBSERVE`, `CANARY_REVIEW`, `DEFENSIVE_POSTURE`)

Mandatory guardrail: this report is an operator-facing reasoning surface, not an execution authority. Any future coupling into allocation or kill-switch logic must pass through the attested release-governance path first.


`python -m strategy_validator.cli.rollout_ops oracle-annual-review-evidence --lane-path docs/artifacts/oracle/ORACLE_SEMIANNUAL_LANE.jsonl --repo-root . --window-size 2 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW.json --markdown-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW.md --output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops verify-oracle-annual-review-evidence docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops oracle-annual-lane-append docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_ANNUAL_REVIEW_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_ANNUAL_LANE_ENTRY.json`

`python -m strategy_validator.cli.rollout_ops oracle-constitutional-digest --lane-path docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl --window-size 3 --output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST.md`

Treat `ANNUAL_EVIDENCE_GAP` as a repair-first signal for missing or unverified semiannual audit artifacts before relying on any constitutional interpretation. Treat `CONSTITUTIONAL_EVIDENCE_GAP`, `CONSTITUTIONAL_REPAIR_CHRONIC`, `CONSTITUTIONAL_RETRAIN_CHRONIC`, and `CONSTITUTIONAL_DEFENSIVE_CHRONIC` as the highest-order advisory governance memory available in the current oracle ladder.

`python -m strategy_validator.cli.rollout_ops oracle-constitutional-digest-evidence --lane-path docs/artifacts/oracle/ORACLE_ANNUAL_LANE.jsonl --repo-root . --window-size 3 --signing-private-key .keys/closure_snapshot_private.pem --public-key .keys/closure_snapshot_public.pem --report-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST.json --markdown-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST.md --output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json --dsse-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json --verification-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops verify-oracle-constitutional-digest-evidence docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json`

`python -m strategy_validator.cli.rollout_ops oracle-constitutional-lane-append docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json --repo-root . --dsse docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --lane-path docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_LANE.jsonl --verification-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.verification.json --output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_LANE_ENTRY.json`

`python -m strategy_validator.cli.rollout_ops oracle-doctrine-lineage-index --repo-root . --search-root docs/artifacts --output docs/artifacts/oracle/ORACLE_DOCTRINE_LINEAGE_INDEX.json --markdown-output docs/artifacts/oracle/ORACLE_DOCTRINE_LINEAGE_INDEX.md`

`python -m strategy_validator.cli.rollout_ops oracle-doctrine-lineage-verify --repo-root . --search-root docs/artifacts --output docs/artifacts/oracle/ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json --markdown-output docs/artifacts/oracle/ORACLE_DOCTRINE_LINEAGE_VERIFICATION.md`

Treat the constitutional digest evidence and constitutional lane as the sealed capstone of the current doctrine ladder. Treat the doctrine lineage index as the operator's audit map across closure, override, oracle, doctrine, and constitutional evidence layers; use it to detect missing sealing steps before relying on long-horizon doctrine summaries. Treat the lineage verification output as the machine judgment: `FULLY_SEALED` means the full closure-to-constitutional ladder is present and parseable, `CONSTITUTIONALLY_REPLAYABLE` means the doctrine stack can be replayed but release-governance coverage is incomplete, and any lower status requires repair before relying on long-horizon conclusions.

`python -m strategy_validator.cli.rollout_ops oracle-constitutional-gate docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.json --repo-root . --search-root docs/artifacts --dsse docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_DIGEST_EVIDENCE.dsse.json --public-key .keys/closure_snapshot_public.pem --minimum-required-seal-status FULLY_SEALED --output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_GATE_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_GATE_REPORT.md`

Treat the constitutional gate as the trust decision for long-horizon doctrine outputs. `TRUSTED` means the constitutional digest passed evidence verification and the doctrine ladder met the required seal threshold; `TRUST_RESTRICTED` means the digest is replayable but the lineage threshold was not met; `UNTRUSTED` means evidence verification or lineage sealing failed and constitutional summaries must not be treated as trusted.

All lineage verification, constitutional gate, derived-view, and checkpoint markdown outputs now append a machine-readable trust explanation tree. Use the dedicated explanation command when you need the same reasoning as standalone JSON/markdown for audit or operator handoff:

`python -m strategy_validator.cli.rollout_ops oracle-explain --report docs/artifacts/oracle/ORACLE_DOCTRINE_LINEAGE_VERIFICATION.json --output docs/artifacts/oracle/ORACLE_TRUST_EXPLANATION_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_TRUST_EXPLANATION_REPORT.md`

For checkpoints, provide both the checkpoint manifest and its verification artifact so the explanation tree can account for evidence verification and doctrine-lineage posture together.

When an operator needs the short answer first, use the dedicated diagnostic surface instead of reading the full explanation tree by hand:

`python -m strategy_validator.cli.rollout_ops oracle-diagnose --report docs/artifacts/oracle/ORACLE_CONSTITUTIONAL_GATE_REPORT.json --output docs/artifacts/oracle/ORACLE_OPERATOR_DIAGNOSTIC_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_OPERATOR_DIAGNOSTIC_REPORT.md`

Use the canonical status pack when you need one auditable bundle that rolls oracle posture, doctrine lineage, constitutional gate state, and release-closure posture together:

`python -m strategy_validator.cli.rollout_ops oracle-status-pack --repo-root . --pack-root docs/artifacts/oracle/status_pack --output docs/artifacts/oracle/ORACLE_STATUS_PACK_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_STATUS_PACK_REPORT.md`

When trust is restricted, untrusted, or blocked, emit a canonical incident pack that preserves the same operator context plus copied source artifacts and a reproducibility digest:

`python -m strategy_validator.cli.rollout_ops oracle-incident-pack --repo-root . --pack-root docs/artifacts/oracle/incident_pack --output docs/artifacts/oracle/ORACLE_INCIDENT_PACK_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_INCIDENT_PACK_REPORT.md`


## Canonical Oracle Event Log workflow

The preferred oracle-memory path is now the canonical **Oracle Event Log** rather than adding new horizon-specific lanes by default.

```bash
python -m strategy_validator.cli.rollout_ops oracle-event-log-append   docs/artifacts/oracle/ORACLE_EVIDENCE.json   --repo-root .   --dsse docs/artifacts/oracle/ORACLE_EVIDENCE.dsse.json   --public-key .keys/closure_snapshot_public.pem   --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl

python -m strategy_validator.cli.rollout_ops oracle-rolling-review   --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl   --horizon weekly   --output docs/artifacts/oracle/ORACLE_DERIVED_VIEW.json   --markdown-output docs/artifacts/oracle/ORACLE_DERIVED_VIEW.md   --checkpoint-metadata-output docs/artifacts/oracle/ORACLE_DERIVED_VIEW.checkpoint.metadata.json

python -m strategy_validator.cli.rollout_ops oracle-rolling-review-checkpoint   --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl   --repo-root .   --horizon weekly   --signing-private-key .keys/closure_snapshot_private.pem   --checkpoint-metadata-output docs/artifacts/oracle/ORACLE_DERIVED_VIEW.checkpoint.metadata.json   --output docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.json   --dsse-output docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.dsse.json   --verification-output docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.verification.json
```

Use `oracle-rolling-review` and `oracle-rolling-review-checkpoint` as the default operator surface for weekly / monthly / quarterly / semiannual / annual / constitutional posture. `oracle-horizon-view` remains available as a lower-level converged surface for custom integrations, while the older weekly/monthly/quarterly/semiannual/annual/constitutional lane commands are **legacy compatibility shims** that remain available for replay and historical continuity, not as the preferred path for new workflows.

Higher-order Event Log surfaces now refresh through one canonical query layer rather than hand-scanning raw JSONL in each command. The query layer supports date-range, strategy, regime, and epistemic-status filters internally, and the CLI can persist `*.checkpoint.metadata.json` sidecars so weekly/monthly/quarterly horizons refresh incrementally from the append-only log instead of rebuilding the full window every time.

Operators can now inspect compacted checkpoint state directly and audit it against canonical replay instead of trusting the sidecar implicitly:

`python -m strategy_validator.cli.rollout_ops oracle-compacted-state-inspect --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl --checkpoint-metadata docs/artifacts/oracle/ORACLE_DERIVED_VIEW.checkpoint.metadata.json --output docs/artifacts/oracle/ORACLE_COMPACTED_STATE_INSPECTION_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_COMPACTED_STATE_INSPECTION_REPORT.md`

`python -m strategy_validator.cli.rollout_ops oracle-replay-audit --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl --checkpoint-metadata docs/artifacts/oracle/ORACLE_DERIVED_VIEW.checkpoint.metadata.json --checkpoint-manifest docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.json --checkpoint-verification docs/artifacts/oracle/ORACLE_EVENT_CHECKPOINT.verification.json --rebuild-parity --output docs/artifacts/oracle/ORACLE_REPLAY_AUDIT_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_REPLAY_AUDIT_REPORT.md`

Use `oracle-compacted-state-inspect` for offset / window / replay-health inspection, and `oracle-replay-audit` when you need a corruption-or-drift check between canonical Event Log replay, compacted checkpoint state, deterministic rebuild parity, and checkpoint bundle artifacts.

Use `oracle-compacted-state-rebuild` when a compacted checkpoint sidecar is stale, drifted, or corrupted and you need to rebuild it from append-only Event Log truth:

`python -m strategy_validator.cli.rollout_ops oracle-compacted-state-rebuild --log-path docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl --checkpoint-metadata docs/artifacts/oracle/ORACLE_DERIVED_VIEW.checkpoint.metadata.json --output docs/artifacts/oracle/ORACLE_COMPACTED_STATE_REBUILD_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_COMPACTED_STATE_REBUILD_REPORT.md`

For a canonical human-facing morning review bundle with machine-readable JSON plus markdown/HTML surfaces and inline provenance digests, emit the briefing pack:

`python -m strategy_validator.cli.rollout_ops oracle-briefing-pack --repo-root . --pack-root docs/artifacts/oracle/briefing_pack --output docs/artifacts/oracle/ORACLE_BRIEFING_PACK_REPORT.json --markdown-output docs/artifacts/oracle/ORACLE_BRIEFING_PACK_REPORT.md --html-output docs/artifacts/oracle/ORACLE_BRIEFING_PACK_REPORT.html`

Each briefing section carries provenance references back to the canonical status pack and, when trust is restricted or blocked, the incident pack digest as well.

Treat weekly/monthly/quarterly doctrine summaries as **derived views** unless a specific downstream policy surface requires them to be signed as first-class evidence.


Legacy compatibility note: `oracle-weekly-digest`, `oracle-monthly-digest`, `oracle-quarterly-review`, `oracle-semiannual-audit`, `oracle-annual-review`, and `oracle-constitutional-digest` accept `--log-path`, and when it is omitted the CLI now auto-detects `docs/artifacts/oracle/ORACLE_EVENT_LOG.jsonl` so those legacy commands still converge onto the canonical Oracle Event Log by default. If you intentionally bypass the canonical Event Log and read a legacy lane directly, you must now pass `--allow-legacy-lane-read`; the command will emit a deprecation warning because those lane reads remain replay/migration surfaces only.


## Strategic capability surfaces

The oracle stack now supports forward-looking strategic synthesis in addition to trust / lineage governance:

- `oracle-sensor-ingest <ORACLE_SENSOR_INGESTION_INPUT.json>` normalizes raw macro, semantic, and microstructure payloads into canonical `ORACLE_ADVISORY_INPUT.json`.
- `oracle-signal-fusion <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_STRATEGIC_FUSION_REPORT.json` with dominant regime, doctrine stress, opportunity score, caution score, and strategic posture.
- `oracle-strategy-health-posterior <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_STRATEGY_HEALTH_POSTERIOR_REPORT.json` with per-strategy confidence decay / recovery state.
- `oracle-opportunity-queue <ORACLE_ADVISORY_INPUT.json>` ranks opportunity, caution, and research-review items from the fused strategic stack.
- `oracle-regime-transition-signal <previous_fusion> <current_fusion>` compares two fusion reports and classifies strategic drift, transition, or structural-break pressure.
- `oracle-thesis-memory <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_THESIS_MEMORY_REPORT.json` so regime, liquidity, doctrine, and strategy theses can strengthen or weaken replayably over time.
- `oracle-scenario-lab <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_SCENARIO_LAB_REPORT.json` by stress-testing the current stack across downside, upside, and doctrine-pressure futures; pass `--scenario-plan` to override the built-in scenario set.
- `oracle-strategy-cohort <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_STRATEGY_COHORT_REPORT.json`, ranking strategies by resilience across posterior confidence, scenario downside floors, queue pressure, and thesis drift.
- `oracle-strategic-briefing <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_STRATEGIC_BRIEFING_REPORT.json` and markdown for morning-review use, now including inline strategy-cohort and scenario-lab sections.
- `oracle-briefing-pack --repo-root ...` now auto-absorbs the latest strategic briefing + thesis memory + thesis graph + scenario lab reports when they exist, so the canonical morning pack surfaces strategic posture, opportunity queue, thesis evolution, dependency-cascade risk, and counterfactual scenario pressure inline.

These strategic surfaces remain advisory-only and are intended to support research prioritization, doctrine review, thesis evolution, and operator attention routing rather than execution authority.

- `oracle-doctrine-adaptation --input ...` emits a clause-level doctrine adaptation advisor and `oracle-strategic-briefing` / `oracle-briefing-pack` now absorb that report when present, surfacing which doctrine assumptions should be monitored, reviewed, adapted, or frozen.
- `oracle-research-planner <ORACLE_ADVISORY_INPUT.json>` emits `ORACLE_RESEARCH_PRIORITY_REPORT.json`, ranking the next investigations from doctrine adaptation, thesis drift, scenario downside, queue pressure, and cohort stress; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that ranked plan when present.


- `oracle-research-execution-memory ORACLE_RESEARCH_PRIORITY_REPORT.json --outcome-input ORACLE_INVESTIGATION_OUTCOME_INPUT.json` records which ranked investigations were actually executed, what they found, and how those outcomes should feed back into thesis memory, cohort ranking, doctrine adaptation, and both strategic briefing surfaces.
- `oracle-thesis-graph ORACLE_ADVISORY_INPUT.json` maps the current dependency graph across theses, doctrine clauses, strategy cohorts, research priorities, and recorded investigation outcomes so the operator can see where cascade risk is concentrated before widening conviction.
- `oracle-strategic-tension ORACLE_ADVISORY_INPUT.json` emits `ORACLE_STRATEGIC_TENSION_REPORT.json`, surfacing where posture, doctrine, scenario stress, cohort resilience, dependency cascades, and investigation outcomes disagree or align too strongly; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that report when present so the morning surface shows contradiction pressure explicitly instead of leaving it implicit.
- `oracle-strategic-narrative ORACLE_ADVISORY_INPUT.json` emits `ORACLE_STRATEGIC_NARRATIVE_REPORT.json`, ranking the main drivers of conviction, fragility, and trust bias across regime posture, contradictions, doctrine pressure, scenarios, cohort resilience, and investigation feedback; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that report when present so the morning surface tells the operator what is actually driving the map instead of only listing its component parts.
- `oracle-contradiction-resolution ORACLE_ADVISORY_INPUT.json` emits `ORACLE_CONTRADICTION_RESOLUTION_REPORT.json`, ranking which contradiction chain should be resolved first for the biggest gain in conviction quality by combining tension severity, narrative fragility, belief-drift state, cascade risk, and matching research urgency; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that report when present so the morning surface tells the operator which contradiction deserves first resolution rather than only that contradictions exist.
- `oracle-strategic-intervention ORACLE_ADVISORY_INPUT.json` emits `ORACLE_STRATEGIC_INTERVENTION_REPORT.json`, simulating which contradiction-resolving intervention is likely to improve conviction quality the most across fragility, doctrine pressure, queue pressure, cohort resilience, and cascade relief; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that report when present so the morning surface shows not only what contradiction matters most, but what downstream improvement the best intervention is expected to buy.
- `oracle-strategic-campaign ORACLE_ADVISORY_INPUT.json` emits `ORACLE_STRATEGIC_CAMPAIGN_REPORT.json`, grouping the strongest interventions, investigations, doctrine actions, and scenario hedges into multi-step strategic campaigns with expected conviction gain, fragility relief, doctrine relief, queue-pressure relief, and cohort recovery upside; both `oracle-strategic-briefing` and `oracle-briefing-pack` now absorb that report when present so the morning surface can show a campaign plan instead of only isolated next moves.
- `oracle-strategic-campaign-state ORACLE_STRATEGIC_CAMPAIGN_REPORT.json --execution-input ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_INPUT.json` emits `ORACLE_STRATEGIC_CAMPAIGN_EXECUTION_REPORT.json`, tracking which campaigns are queued, active, blocked, drifting, completed, or invalidated; the strategic briefing and canonical morning pack absorb that report when present so the operator sees which multi-step campaign is actually underway, stuck, or finished rather than only the plan.

## Strategic memory horizon

Use `oracle-strategic-memory-horizon` to compare the latest strategic narrative report against one or more earlier narrative reports and emit a replayable belief-drift timeline. The resulting `ORACLE_STRATEGIC_MEMORY_HORIZON_REPORT.json` can be passed into `oracle-strategic-briefing` via `--strategic-memory-horizon-report` and is auto-absorbed by `oracle-briefing-pack` when present.
