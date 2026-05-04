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


## Deployment readiness and ledger backup

Runtime readiness answers whether adjudication is lawful. Deployment readiness additionally checks operator-release hygiene: ledger database existence, schema compatibility, hash-chain integrity, backup target configuration, mutation-auth posture, and private-key material under the repository root.

Set a deployment backup target before production runs:

`STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/absolute/path/to/ledger_backups`

Verify the configured ledger before a release or handoff:

`python -m strategy_validator.cli.ledger_ops verify --database-path /absolute/path/forensic_ledger.sqlite3 --json`

Create a timestamped SQLite backup that is verified before and after copy:

`python -m strategy_validator.cli.ledger_ops backup --database-path /absolute/path/forensic_ledger.sqlite3 --backup-dir /absolute/path/ledger_backups --json`

Restore a verified backup into a new destination before promoting a recovered runtime:

`python -m strategy_validator.cli.ledger_ops restore --backup-path /absolute/path/ledger_backups/forensic_ledger_20260429T030000Z.sqlite3 --database-path /absolute/path/restored_forensic_ledger.sqlite3 --json`

The restore command verifies the backup before copying, writes through a temporary restore file, verifies the restored destination afterward, and refuses to overwrite an existing destination unless `--allow-overwrite` is explicit.

A failed hash-chain verification, missing ledger DB, unwritable backup directory, restore verification failure, or private signing key material under repo-controlled paths is deployment-blocking.

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


> **Key hygiene:** private signing keys are operator-local secrets. Keep them under `.keys/` or a deployment secrets manager only. Do not commit private PEM material under `docs/`, `docs/artifacts/`, or release bundles. Historical closure artifacts in this repository are public evidence/test fixtures only unless re-signed with an operator-controlled private key.

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

## Deployment readiness preflight

Before exposing the API or handing off a release candidate, run the deployment readiness tier in addition to the normal startup check:

```bash
strategy-validator-startup-check --deployment-json --repo-root .
strategy-validator-startup-check --deployment-summary-json --repo-root .
```

The full deployment tier is broader than adjudication readiness. It reports runtime readiness, ledger database existence, schema compatibility, hash-chain integrity, backup directory configuration, backup directory writability, and repository private-key hygiene. The summary form emits the compact operator decision fields: `recommended_action`, `blocker_codes`, `warning_codes`, and `failed_checks`. Operators should treat `BLOCKED` / `BLOCK_DEPLOYMENT` as a no-deploy state. `DEGRADED` requires an explicit operator memo before proceeding.

The API exposes the same preflight payloads at:

```text
GET /readiness/deployment
GET /readiness/deployment/summary
```

Use this endpoint for dashboards and release checks. Do not substitute it for `strategy-validator-ledger-ops backup`; readiness confirms the backup target is configured and writable, while the ledger ops command performs the actual verified backup.

## Research OS runtime demo and thesis mutation loop

Paper and research **artifacts only**; these commands do **not** adjudicate, trade live, or write the ledger.

- `strategy-validator-research-os-runtime-demo` — Writes `research_os_runtime/latest/runtime_demo_manifest.json` under `STRATEGY_VALIDATOR_ARTIFACT_ROOT` (see `docs/strategy_lab/RESEARCH_OPERATING_SYSTEM.md`). Add **`--full-research-os-cycle`** to also emit thesis to Oracle mutation proposals to **proposed** next batch spec under `<artifact_root>/research_os_runtime/` (`next_batch_spec_proposed.json`, `thesis_mutation_loop_report.json`).
- `strategy-validator-thesis-mutation-batch-loop` — Offline follow-on from a completed run: **`--batch-summary`** path to `batch_summary.json`, **`--next-batch-spec-output`** path for a proposed `StrategyBatchSpec` JSON, optional **`--loop-report-output`** for the loop report. Operator must review artifacts before running `strategy-validator-strategy-batch-run` on the proposed spec.

## Semantic research evidence preflight

Before a semantic tribunal feature is used as adjudication evidence, route it through the application-layer bridge instead of appending ad-hoc payloads to an experiment manifest.

Canonical sequence:

1. Build or load an `ExperimentManifest` with explicit `evaluation_time_utc` and `market_data_subject_id`.
2. Materialize the tribunal artifact through `materialize_semantic_feature_for_proposal(...)` so PIT join provenance is captured.
3. Build evidence through `build_semantic_materialization_evidence(...)` or attach through `attach_semantic_materialization_evidence(...)`.
4. Verify with `verify_semantic_materialization_evidence(...)` before adjudication.
5. Preserve the bundle-level `data_spine_seal`; it fingerprints the PIT provenance used by the semantic research lane.

The bridge intentionally does **not** adjudicate and does **not** write the ledger. It only creates checksummed evidence and data-spine lineage that the canonical orchestrator may evaluate later.

### Semantic research preflight

Before semantic tribunal features are allowed into an adjudication manifest, run the bounded research preflight. This path is deliberately read/application-layer only: it materializes one tribunal feature through the PIT join engine, builds deterministic adjudication evidence, verifies the checksum and identity alignment, and optionally writes an updated manifest with evidence plus a Data Spine seal. It does **not** adjudicate and does **not** write the ledger.

```bash
strategy-validator-research-preflight \
  --proposal proposal.json \
  --artifact semantic-artifact.json \
  --published-at 2026-04-28T11:45:00Z \
  --available-at 2026-04-28T11:50:00Z \
  --write-updated-proposal proposal.with-semantic-evidence.json
```

For API/BFF callers, use:

```text
POST /research/semantic-preflight
```

The returned `semantic_research_preflight/v1` report must show `evidence_verified=true` and `recommended_action=ATTACH_TO_ADJUDICATION_EVIDENCE` before the proposal is passed to adjudication. If the report returns `BLOCK_RESEARCH_INTAKE`, the proposal remains research-only until the issue codes are resolved.

### Semantic research integrity gate

After semantic evidence has been attached to a proposal and before the proposal is handed to adjudication, verify the proposal-level semantic evidence integrity gate:

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

The gate checks that attached semantic materialization evidence is checksummed, belongs to the same experiment, has complete PIT provenance, and that the PIT lineage is represented in the proposal's `data_spine_seal`. It is intentionally read-only and does not adjudicate or write the ledger.

For API/BFF callers, use:

```text
POST /research/semantic-integrity
```

The returned `semantic_research_integrity/v1` report must show `verified=true` and `recommended_action=READY_FOR_ADJUDICATION_PREFLIGHT`. `BLOCK_ADJUDICATION_PREFLIGHT` means the proposal should not enter the validator orchestrator until the listed issue codes are resolved.

### Semantic research adjudication guard

The validator orchestrator now evaluates `SemanticResearchIntegrity` whenever a proposal carries semantic artifacts or semantic materialization evidence. Non-semantic strategies pass this gate as `NO_SEMANTIC_RESEARCH_LANE`; semantic lanes must carry verified materialization evidence and, when materialization evidence is present, a matching `data_spine_seal`.

For compact operator checks, use the summary output before handing a manifest to adjudication:

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --verify-summary-json
```

For API/BFF callers, use:

```text
POST /research/semantic-integrity/summary
```

The summary is intentionally small: `verified`, `recommended_action`, `semantic_evidence_count`, `data_spine_seal_present`, `blocker_codes`, and `warning_codes`. A non-empty `blocker_codes` list means the proposal will be quarantined by the semantic research integrity gate if it enters adjudication.

### Semantic adjudication-gate summary artifact

For handoff packets and UI/BFF preflight cards, prefer the adjudication-gate summary over the generic integrity summary when the next action is validator handoff:

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --adjudication-gate-summary-json \
  --write-report semantic-adjudication-gate-summary.json
```

For API/BFF callers, use:

```text
POST /research/semantic-adjudication-gate/summary
```

The returned `semantic_research_adjudication_gate_summary/v1` payload mirrors the orchestrator gate semantics without mutating the proposal or writing the ledger. It reports `gate_passed`, `gate_reason`, `recommended_action`, semantic lane presence, evidence counts, Data Spine seal presence, and blocker/warning codes. Treat `QUARANTINE_BEFORE_ADJUDICATION` as a hard handoff blocker.

### Semantic adjudication gate artifact

After semantic research evidence has been attached and verified, operators can seal the exact pre-adjudication semantic gate decision as a machine-readable artifact. This artifact is read-only evidence; it does not adjudicate and it does not write the ledger.

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --adjudication-gate-artifact-json \
  --write-report semantic-adjudication-gate-artifact.json
```

Verify the artifact before handoff, optionally against the proposal it was generated from:

```bash
strategy-validator-research-preflight \
  --verify-gate-artifact semantic-adjudication-gate-artifact.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API equivalents:

- `POST /research/semantic-adjudication-gate/artifact`
- `POST /research/semantic-adjudication-gate/artifact/verify`

The artifact records the gate summary, proposal semantic-input digest, semantic evidence checksums, Data Spine fingerprint, and a canonical payload checksum. If the proposal or attached semantic evidence changes, verification must fail and the artifact must be rebuilt.

### Semantic adjudication readiness handoff

Before handing a semantically enriched proposal to adjudication, produce a final readiness report. This report combines the canonical semantic integrity gate with optional verification of the sealed semantic adjudication-gate artifact.

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --adjudication-readiness-json \
  --gate-artifact semantic-adjudication-gate-artifact.json \
  --require-gate-artifact \
  --write-report semantic-adjudication-readiness.json
```

The API equivalent is:

```text
POST /research/semantic-adjudication-readiness
```

Use `--require-gate-artifact` for release/adjudication handoffs that must be replayable from archived operator evidence. A semantic lane with no gate artifact must remain blocked until the artifact is regenerated and verified against the current proposal payload.

### Semantic adjudication handoff artifact

For release-quality semantic proposals, archive a sealed handoff artifact rather than only the readiness report. The handoff artifact packages the final readiness report, optional semantic gate artifact, proposal semantic-input digest, and a canonical payload checksum.

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --adjudication-handoff-artifact-json \
  --gate-artifact semantic-adjudication-gate-artifact.json \
  --require-gate-artifact \
  --write-report semantic-adjudication-handoff-artifact.json
```

Verify the handoff artifact before invoking the adjudicator:

```bash
strategy-validator-research-preflight \
  --verify-handoff-artifact semantic-adjudication-handoff-artifact.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API equivalents:

- `POST /research/semantic-adjudication-handoff/artifact`
- `POST /research/semantic-adjudication-handoff/artifact/verify`

Treat `semantic_adjudication_handoff_artifact_verification/v1.verified=false` as a hard stop. It means the proposal, embedded gate artifact, readiness report, or canonical checksum has drifted and the handoff packet must be regenerated before adjudication.

### Semantic adjudication bundle workflow

After generating and verifying the semantic gate artifact and the semantic handoff artifact, operators can seal the compact final handoff bundle. The bundle binds the proposal semantic-input digest, the gate artifact, the handoff artifact, semantic evidence checksums, and the Data Spine fingerprint.

Generate the bundle:

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --adjudication-bundle-json \
  --require-gate-artifact \
  --write-report semantic-adjudication-bundle.json
```

Verify the bundle before handing the proposal to adjudication:

```bash
strategy-validator-research-preflight \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle`
- `POST /research/semantic-adjudication-bundle/verify`

A verified bundle is not a ledger write and does not grant authority. It is an operator handoff proof: the validator/orchestrator still owns adjudication and ledger mutation.

## Semantic adjudication bundle summary and manifest

After generating a semantic adjudication bundle, operators should emit a compact summary and a portable manifest before handing the proposal to adjudication or archiving the handoff pack.

Summary:

```bash
strategy-validator-research-preflight \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --bundle-summary-json \
  --write-report semantic-adjudication-bundle-summary.json
```

Manifest:

```bash
strategy-validator-research-preflight \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --bundle-manifest-json \
  --write-report semantic-adjudication-bundle-manifest.json
```

Manifest verification:

```bash
strategy-validator-research-preflight \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/summary`
- `POST /research/semantic-adjudication-bundle/manifest`
- `POST /research/semantic-adjudication-bundle/manifest/verify`

The manifest is intentionally compact: it stores checksums, artifact ids, semantic evidence checksums, Data Spine fingerprint, and the operator summary, not the full proposal. Treat a failed manifest verification as a hard stop for adjudication handoff.

## Semantic adjudication bundle release preflight

Before a semantic research handoff bundle is attached to an adjudication request or release packet, run the final bundle release preflight. This check composes bundle verification, optional manifest verification, and final adjudication-readiness state into one compact operator/CI decision object.

Recommended strict form:

```bash
strategy-validator-research-preflight \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --bundle-release-preflight-json \
  --write-report semantic-adjudication-bundle-release-preflight.json
```

The preflight blocks if the bundle or manifest drifts from the proposal, if the manifest is required but missing, or if the embedded readiness report is not ready for adjudication. Use `--allow-missing-bundle-manifest` only for local diagnostics; release and CI flows should require the manifest.

API equivalent:

```text
POST /research/semantic-adjudication-bundle/release-preflight
```

The response schema is `semantic_adjudication_bundle_release_preflight/v1` and exposes `recommended_action`, `blocker_codes`, `bundle_verified`, `manifest_verified`, and `ready_for_adjudication` for CI/release gates.

### Semantic adjudication release index

After generating and verifying the semantic adjudication bundle and its portable manifest, emit a compact release index for CI/release handoff. The release index does not embed the full proposal; it binds the bundle checksum, manifest checksum, gate artifact, handoff artifact, semantic evidence checksums, Data Spine fingerprint, and final release preflight recommendation.

Generate the index:

```bash
strategy-validator-research-preflight \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --bundle-release-index-json \
  --write-report semantic-adjudication-release-index.json
```

Verify the index before release handoff:

```bash
strategy-validator-research-preflight \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/release-index`
- `POST /research/semantic-adjudication-bundle/release-index/verify`

Use the release index as the top-level artifact in CI/release notes. If verification fails, rebuild the semantic gate artifact, handoff artifact, bundle, manifest, and index from the current proposal rather than editing JSON by hand.

### Semantic adjudication release capsule

After the release index verifies, emit the final semantic release capsule. This is the smallest operator/CI receipt that says “this release index was verified against the current bundle/manifest/proposal context and is ready for adjudication handoff.” It is intended to be archived with release notes or used as a terminal CI artifact.

Generate the capsule:

```bash
strategy-validator-research-preflight \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --release-capsule-json \
  --write-report semantic-adjudication-release-capsule.json
```

Verify the capsule:

```bash
strategy-validator-research-preflight \
  --verify-release-capsule semantic-adjudication-release-capsule.json \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/release-capsule`
- `POST /research/semantic-adjudication-bundle/release-capsule/verify`
- `POST /research/semantic-adjudication-bundle/release-capsule/summary`

Generate the compact capsule summary for CI logs or operator dashboards:

```bash
strategy-validator-research-preflight \
  --verify-release-capsule semantic-adjudication-release-capsule.json \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --release-capsule-summary-json \
  --write-report semantic-adjudication-release-capsule-summary.json
```

Treat `semantic_adjudication_release_capsule/v1` as the terminal semantic-lane handoff receipt and `semantic_adjudication_release_capsule_summary/v1` as the compact status view. If capsule verification fails, rebuild from the proposal outward: gate artifact → handoff artifact → bundle → manifest → release preflight → release index → release capsule. Do not manually patch the capsule checksum.

### Semantic adjudication release decision record

After the release capsule verifies, emit a terminal decision record. This record does not adjudicate and does not write the ledger; it records the operator or CI decision over the sealed capsule summary so the semantic-lane handoff has a final human/machine-readable receipt.

Generate the decision record:

```bash
strategy-validator-research-preflight \
  --verify-release-capsule semantic-adjudication-release-capsule.json \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --release-decision-record-json \
  --decision ACCEPT_FOR_ADJUDICATION \
  --decided-by ci-release-gate \
  --decision-reason "semantic capsule verified against current proposal" \
  --write-report semantic-adjudication-release-decision-record.json
```

Verify the decision record:

```bash
strategy-validator-research-preflight \
  --verify-release-decision-record semantic-adjudication-release-decision-record.json \
  --verify-release-capsule semantic-adjudication-release-capsule.json \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/release-decision-record`
- `POST /research/semantic-adjudication-bundle/release-decision-record/verify`

Only `ACCEPT_FOR_ADJUDICATION` is marked `decision_allowed=true`, and only when the capsule summary is ready. If the capsule is unready, the builder records a blocking decision by default; an attempted accept on an unready capsule emits `SEMANTIC_RELEASE_DECISION_ACCEPTED_UNREADY_CAPSULE` and the verifier blocks the record.

Generate the compact terminal decision-record summary for CI logs, release comments, or operator dashboards:

```bash
strategy-validator-research-preflight \
  --verify-release-decision-record semantic-adjudication-release-decision-record.json \
  --verify-release-capsule semantic-adjudication-release-capsule.json \
  --verify-bundle-release-index semantic-adjudication-release-index.json \
  --verify-bundle semantic-adjudication-bundle.json \
  --verify-bundle-manifest semantic-adjudication-bundle-manifest.json \
  --verify-proposal-only proposal.with-semantic-evidence.json \
  --release-decision-record-summary-json \
  --write-report semantic-adjudication-release-decision-record-summary.json
```

Additional API surface:

- `POST /research/semantic-adjudication-bundle/release-decision-record/summary`

Use `semantic_adjudication_release_decision_record_summary/v1` as the terminal CI/operator status object. `recommended_action=HAND_OFF_TO_VALIDATOR_ADJUDICATION` is the only positive handoff state. Any other value means the sealed semantic chain should be rebuilt, reverified, or respected as a recorded block decision before the validator authority path is invoked.

### Semantic release decision ledger

After generating a terminal semantic release decision record, archive a chained decision ledger so CI or an operator can prove which decision record was terminal at handoff time. This ledger is an operator-side handoff artifact; it does **not** write to the canonical validator ledger.

Generate a ledger from one or more decision records:

```bash
strategy-validator-research-preflight \
  --release-decision-record semantic-adjudication-release-decision-record.json \
  --release-decision-ledger-json \
  --write-report semantic-adjudication-release-decision-ledger.json
```

Verify the ledger, optionally replaying it against the source decision records:

```bash
strategy-validator-research-preflight \
  --verify-release-decision-ledger semantic-adjudication-release-decision-ledger.json \
  --release-decision-record semantic-adjudication-release-decision-record.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/release-decision-ledger`
- `POST /research/semantic-adjudication-bundle/release-decision-ledger/verify`

The verifier fails closed on checksum drift, non-contiguous entry indexes, previous-hash mismatches, duplicate decision ids, record drift, and multiple accepted decisions in one semantic release ledger.

Generate the compact decision-ledger summary for CI logs, release comments, or operator dashboards:

```bash
strategy-validator-research-preflight \
  --verify-release-decision-ledger semantic-adjudication-release-decision-ledger.json \
  --release-decision-record semantic-adjudication-release-decision-record.json \
  --release-decision-ledger-summary-json \
  --write-report semantic-adjudication-release-decision-ledger-summary.json
```

Additional API surface:

- `POST /research/semantic-adjudication-bundle/release-decision-ledger/summary`

Use `semantic_adjudication_release_decision_ledger_summary/v1` as the lightweight terminal ledger status object. `recommended_action=HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR` is the only positive terminal handoff state. Any verification issue, empty ledger, multiple accepted decisions, or terminal block decision keeps the semantic chain outside the validator authority path until rebuilt or explicitly respected as blocked.

## Semantic release handoff certificate

After the semantic release decision ledger has been generated and summarized, emit a terminal handoff certificate before passing the proposal into validator adjudication. The certificate is intentionally portable and read-only: it does not write the canonical validator ledger. It seals the verified decision-ledger summary and records the operator or CI actor issuing the handoff.

Generate the certificate:

```bash
strategy-validator-research-preflight \
  --verify-release-decision-ledger semantic-adjudication-release-decision-ledger.json \
  --release-decision-record semantic-adjudication-release-decision-record.json \
  --release-handoff-certificate-json \
  --issued-by ci-release-gate \
  --write-report semantic-adjudication-release-handoff-certificate.json
```

Verify the certificate before validator handoff:

```bash
strategy-validator-research-preflight \
  --verify-release-handoff-certificate semantic-adjudication-release-handoff-certificate.json \
  --verify-release-decision-ledger semantic-adjudication-release-decision-ledger.json \
  --release-decision-record semantic-adjudication-release-decision-record.json
```

Emit the compact CI/operator summary:

```bash
strategy-validator-research-preflight \
  --verify-release-handoff-certificate semantic-adjudication-release-handoff-certificate.json \
  --verify-release-decision-ledger semantic-adjudication-release-decision-ledger.json \
  --release-decision-record semantic-adjudication-release-decision-record.json \
  --release-handoff-certificate-summary-json \
  --write-report semantic-adjudication-release-handoff-certificate-summary.json
```

The only positive terminal recommendation is `HAND_OFF_TO_VALIDATOR_ADJUDICATION`. Any checksum drift, ledger mismatch, unverified certificate, or non-accepted terminal decision must be treated as a blocking release condition.

API equivalents:

- `POST /research/semantic-adjudication-bundle/release-handoff-certificate`
- `POST /research/semantic-adjudication-bundle/release-handoff-certificate/verify`
- `POST /research/semantic-adjudication-bundle/release-handoff-certificate/summary`

### Semantic release handoff certificate as validator evidence

After the terminal semantic release handoff certificate verifies, operators can wrap it as ordinary validator-facing `Evidence`. This creates the explicit bridge from the sealed semantic release chain into the canonical adjudication input stream without granting ledger write authority.

```bash
strategy-validator-research-preflight \
  --verify-release-handoff-certificate semantic-adjudication-release-handoff-certificate.json \
  --release-handoff-certificate-evidence-json \
  --write-report semantic-release-handoff-certificate-evidence.json

strategy-validator-research-preflight \
  --verify-release-handoff-certificate-evidence semantic-release-handoff-certificate-evidence.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/release-handoff-certificate/evidence`
- `POST /research/semantic-adjudication-bundle/release-handoff-certificate/evidence/verify`

The validator orchestrator records a `SemanticReleaseHandoffCertificate` gate. Absence of this evidence remains non-blocking for non-release semantic lanes, but any supplied certificate evidence must verify and must allow handoff, otherwise the proposal is quarantined.


### Semantic handoff certificate evidence summary

After converting a terminal semantic release handoff certificate into validator-facing `Evidence`, operators can emit a compact summary before handing the proposal to adjudication:

```bash
strategy-validator-research-preflight \
  --verify-release-handoff-certificate-evidence semantic-release-handoff-certificate-evidence.json \
  --release-handoff-certificate-evidence-summary-json \
  --write-report semantic-release-handoff-certificate-evidence-summary.json
```

The equivalent API endpoint is:

```text
POST /research/semantic-adjudication-bundle/release-handoff-certificate/evidence/summary
```

The only positive terminal action from this summary is `HAND_OFF_CERTIFICATE_EVIDENCE_TO_VALIDATOR`. Any checksum drift, invalid embedded certificate, disabled handoff flag, or schema/source mismatch must be treated as a blocker and the evidence must be rebuilt from the sealed certificate chain.

### Semantic validator handoff packet

Once the terminal handoff certificate has been converted into ordinary validator-facing `Evidence`, emit a portable handoff packet before passing the object into validator ingestion. The packet binds the exact Evidence JSON, its compact summary, certificate id/checksum, handoff flag, and a canonical packet checksum.

```bash
strategy-validator-research-preflight \
  --verify-release-handoff-certificate-evidence semantic-release-handoff-certificate-evidence.json \
  --validator-handoff-packet-json \
  --write-report semantic-validator-handoff-packet.json
```

Verify the packet, optionally against the source Evidence file:

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-release-handoff-certificate-evidence semantic-release-handoff-certificate-evidence.json
```

Emit the compact packet summary:

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-release-handoff-certificate-evidence semantic-release-handoff-certificate-evidence.json \
  --validator-handoff-packet-summary-json \
  --write-report semantic-validator-handoff-packet-summary.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-handoff-packet`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/verify`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/summary`

The only positive packet recommendation is `HAND_OFF_PACKET_TO_VALIDATOR`. Packet checksum drift, embedded Evidence drift, source Evidence mismatch, invalid certificate Evidence, or a disabled handoff flag must block validator handoff.

### Semantic validator handoff packet ingress preflight

Before a sealed semantic validator handoff packet is treated as ready for the validator path, run the ingress preflight. This verifies the packet, verifies the embedded validator-facing `Evidence`, and—by default—proves that the same evidence checksum is already attached to the proposal evidence bundle.

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-handoff-packet-ingress-json \
  --write-report semantic-validator-handoff-packet-ingress.json
```

For CI/operator dashboards, emit the compact summary:

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-handoff-packet-ingress-summary-json \
  --write-report semantic-validator-handoff-packet-ingress-summary.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/summary`

The only positive terminal recommendation is `HAND_OFF_PACKET_EVIDENCE_TO_VALIDATOR`. Missing proposal evidence, packet drift, invalid embedded certificate evidence, or mismatched experiment IDs must block validator handoff.

### Semantic validator handoff packet ingress certificate

After the ingress preflight passes, seal the result into a portable validator-ingress certificate. This gives CI and operators a stable, checksummed artifact proving that the packet was verified, the embedded validator-facing Evidence was verified, and the packet Evidence was present on the proposal at the time of handoff.

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-handoff-ingress-certificate-json \
  --issued-by ci-release-gate \
  --write-report semantic-validator-handoff-ingress-certificate.json
```

Verify the certificate against the source packet and proposal:

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-ingress-certificate semantic-validator-handoff-ingress-certificate.json \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json
```

Emit the compact certificate summary:

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-ingress-certificate semantic-validator-handoff-ingress-certificate.json \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-handoff-ingress-certificate-summary-json \
  --write-report semantic-validator-handoff-ingress-certificate-summary.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/verify`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/certificate/summary`

The only positive certificate recommendation is `HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR`. Any packet checksum drift, report drift, missing proposal evidence, experiment mismatch, or non-handoff ingress report must block validator handoff.

### Semantic validator-ingress acceptance record

After the validator handoff packet ingress certificate verifies cleanly, issue a terminal acceptance record before invoking the validator adjudication command. This makes the final operator/CI acceptance explicit and replayable instead of implied by a passing certificate.

```bash
strategy-validator-research-preflight \
  --verify-validator-handoff-ingress-certificate semantic-validator-handoff-ingress-certificate.json \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-ingress-acceptance-record-json \
  --accepted-by ci-release-gate \
  --acceptance-reason "sealed semantic packet ready for validator adjudication" \
  --write-report semantic-validator-ingress-acceptance-record.json
```

Verify or summarize the record before handoff:

```bash
strategy-validator-research-preflight \
  --verify-validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json \
  --verify-validator-handoff-ingress-certificate semantic-validator-handoff-ingress-certificate.json \
  --verify-validator-handoff-packet semantic-validator-handoff-packet.json \
  --verify-proposal-only proposal.with-handoff-evidence.json \
  --validator-ingress-acceptance-record-summary-json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record/verify`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-record/summary`

The positive terminal action is `SUBMIT_ACCEPTED_SEMANTIC_PACKET_TO_VALIDATOR`. Any checksum drift, unready certificate, or non-handoff certificate summary must be treated as a block.

### Semantic validator-ingress acceptance ledger

After an ingress acceptance record is created, operators can chain one or more
terminal acceptance records into a portable append-only acceptance ledger. This
ledger is still outside the canonical validator ledger; it is a CI/operator
handoff receipt that proves which semantic validator-ingress acceptance state was
terminal before invoking adjudication.

Build the ledger:

```bash
strategy-validator-research-preflight \
  --validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json \
  --validator-ingress-acceptance-ledger-json \
  --write-report semantic-validator-ingress-acceptance-ledger.json
```

Verify the ledger:

```bash
strategy-validator-research-preflight \
  --verify-validator-ingress-acceptance-ledger semantic-validator-ingress-acceptance-ledger.json \
  --validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json
```

Emit the compact CI/operator summary:

```bash
strategy-validator-research-preflight \
  --verify-validator-ingress-acceptance-ledger semantic-validator-ingress-acceptance-ledger.json \
  --validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json \
  --validator-ingress-acceptance-ledger-summary-json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger/verify`
- `POST /research/semantic-adjudication-bundle/validator-handoff-packet/ingress/acceptance-ledger/summary`

A positive terminal summary action is
`SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR`. Empty ledgers, checksum drift,
duplicate accepts, sequence gaps, or terminal blocked records must be treated as
`RESPECT_TERMINAL_VALIDATOR_INGRESS_BLOCK_OR_REBUILD_LEDGER`.

### Semantic validator submission packet

After the terminal validator-ingress acceptance ledger is verified, seal the final validator submission intent into a compact packet. This packet is the operator/CI handoff artifact for invoking validator adjudication; it is still evidence-only and does not grant ledger write authority.

Generate the packet:

```bash
strategy-validator-research-preflight \
  --verify-validator-ingress-acceptance-ledger semantic-validator-ingress-acceptance-ledger.json \
  --validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json \
  --validator-submission-packet-json \
  --submitted-by ci-release-gate \
  --submission-reason "terminal semantic ingress accepted" \
  --write-report semantic-validator-submission-packet.json
```

Verify and summarize it before adjudication:

```bash
strategy-validator-research-preflight \
  --verify-validator-submission-packet semantic-validator-submission-packet.json \
  --verify-validator-ingress-acceptance-ledger semantic-validator-ingress-acceptance-ledger.json \
  --validator-ingress-acceptance-record semantic-validator-ingress-acceptance-record.json \
  --validator-submission-packet-summary-json
```

API surfaces:

- `POST /research/semantic-adjudication-bundle/validator-submission-packet`
- `POST /research/semantic-adjudication-bundle/validator-submission-packet/verify`
- `POST /research/semantic-adjudication-bundle/validator-submission-packet/summary`

Positive terminal action is `SUBMIT_SEMANTIC_VALIDATOR_PACKET_TO_ADJUDICATION`. Any mismatch, unaccepted terminal ingress ledger, checksum drift, or embedded summary drift must be treated as a blocker and rebuilt before validator execution.

### Semantic validator submission-packet Evidence

After a terminal semantic validator submission packet is built and verified, operators can convert it into ordinary validator `Evidence`. This keeps the final handoff inside the normal evidence stream while preserving the authority boundary: the Evidence does not write to the ledger and the validator orchestrator still verifies it before adjudication.

Generate validator-facing submission Evidence:

```bash
strategy-validator-research-preflight \
  --verify-validator-submission-packet semantic-validator-submission-packet.json \
  --validator-submission-packet-evidence-json \
  --write-report semantic-validator-submission-packet-evidence.json
```

Verify or summarize the Evidence before adjudication:

```bash
strategy-validator-research-preflight \
  --verify-validator-submission-packet-evidence semantic-validator-submission-packet-evidence.json \
  --validator-submission-packet-evidence-summary-json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-submission-packet/evidence`
- `POST /research/semantic-adjudication-bundle/validator-submission-packet/evidence/verify`
- `POST /research/semantic-adjudication-bundle/validator-submission-packet/evidence/summary`

The adjudication orchestrator treats this Evidence as optional for ordinary proposals. If the Evidence is supplied, the `SemanticValidatorSubmissionPacketEvidence` gate verifies its schema, checksum, embedded submission packet, summary, and readiness flag. Invalid supplied Evidence quarantines the proposal.

### Semantic validator submission readiness preflight

After producing validator-facing submission-packet `Evidence`, run the final proposal-level readiness preflight before invoking the normal adjudication path. This check is intentionally narrow: it verifies the terminal submission Evidence and confirms that the exact Evidence id/checksum is attached to the proposal's `evidence_bundle.evidence_items`.

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-submission-evidence.json \
  --validator-submission-readiness-json \
  --write-report semantic-validator-submission-readiness.json
```

For CI/operator dashboards, emit the compact summary:

```bash
strategy-validator-research-preflight \
  --verify-proposal-only proposal.with-submission-evidence.json \
  --validator-submission-readiness-summary-json \
  --write-report semantic-validator-submission-readiness-summary.json
```

API equivalents:

- `POST /research/semantic-adjudication-bundle/validator-submission/readiness`
- `POST /research/semantic-adjudication-bundle/validator-submission/readiness/summary`

Positive terminal action is `SUBMIT_PROPOSAL_TO_VALIDATOR_ADJUDICATION`. Any missing terminal submission Evidence, checksum drift, invalid embedded packet, or Evidence not attached to the proposal remains fail-closed.

## Control-plane event envelopes

Selected control-plane workflows now emit a canonical event-envelope sidecar next to rendered operator artifacts. The first event-envelope-backed workflow is operator decision execution:

- JSON rendering: `ORACLE_OPERATOR_DECISION_EXECUTION.json`
- Markdown rendering: `ORACLE_OPERATOR_DECISION_EXECUTION.md`
- Event sidecar: `ORACLE_OPERATOR_DECISION_EXECUTION.event.json`

The sidecar records the producer, event type, actor, target, idempotency key, evidence references, and canonical payload digest. It is not yet a ledger write. Treat it as the transition format for moving control-plane workflows from file-first materialization toward event-backed projections.


### Control-plane event-backed artifact sidecars

Some control-plane workflows now emit event-shaped sidecars in addition to the
operator JSON/Markdown artifacts. For example, decision execution materializes:

```text
ORACLE_OPERATOR_DECISION_EXECUTION.event.json
ORACLE_OPERATOR_DECISION_EXECUTION.json
ORACLE_OPERATOR_DECISION_EXECUTION.md
```

The `.event.json` file is the canonical transition shape toward an event-backed
control-plane stream. It includes the event type, producer, actor, target,
idempotency key, payload digest, evidence refs, and payload. Operators should
treat the JSON/Markdown files as rendered evidence and the event sidecar as the
replayable identity of the materialization.

This sidecar is not yet a ledger mutation. Ledger-backed operator control-plane
events remain a later hardening step.


## Slice 21: event journal bridge and sidecar replay

Control-plane event sidecars can now be replayed with `build_control_plane_event_sidecar_replay_report(...)` and materialized as a projection artifact with `write_control_plane_event_sidecar_replay_report(...)`. Event-backed materializers may opt in to durable operator journal recording via `append_to_operator_journal=True`; this writes the verified event envelope to `operator_action_events` as a `control-plane-event` action while preserving the `.event.json` sidecar as a filesystem rendering.

The production smoke script also accepts `--restore-drill-backup-path` plus `--restore-drill-database-path` for a verified restore drill that can be paired with readiness checks.

### Control-plane event sidecar replay

For control-plane workflows that emit `.event.json` sidecars, replay the event sidecars before treating the rendered JSON/Markdown artifacts as trustworthy operator evidence:

```bash
strategy-validator-control-plane-event-sidecars replay \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-sidecar-replay.json \
  --fail-on-rejected \
  --json
```

When the workflow also records `control-plane-event` entries into the operator action journal, reconcile sidecars against the journal:

```bash
strategy-validator-control-plane-event-sidecars reconcile \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-reconciliation.json \
  --fail-on-drift \
  --json
```

`replay` proves the sidecar payloads verify. `reconcile` proves the filesystem sidecars and durable journaled control-plane events agree by event id and payload digest.

### Operator action journal chain verification

The operator action journal is now independently verifiable from the main decision ledger. Use this check after UI command replay tests, control-plane event journal recording, restore drills, or any manual inspection of `operator_action_events`:

```bash
strategy-validator-ledger-ops verify-operator-actions \
  --database-path /var/lib/strategy-validator/ledger.sqlite3 \
  --json
```

The command emits `ledger_ops_operator_action_chain_verify/v1` with `event_count`, `issue_count`, and concrete chain issues. A non-zero exit means the operator-action journal cannot be trusted for replay until the database is restored from a verified backup or explicitly investigated.

### Semantic validator submission stage ownership

The terminal semantic validator acceptance/submission helpers now live in `strategy_validator/application/research_integrity_validator_submission.py` and remain re-exported by `strategy_validator.application.research_integrity` for compatibility. New code should import the stage module directly; the legacy module is now a compatibility facade over the decomposed research-integrity stages.

### Control-plane sidecar reconciliation with operator-chain verification

Run replay first when validating filesystem event sidecars:

```bash
strategy-validator-control-plane-event-sidecars replay \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-sidecar-replay.json \
  --fail-on-rejected \
  --json
```

Then reconcile sidecars against journaled `control-plane-event` entries and verify the operator action journal chain:

```bash
strategy-validator-control-plane-event-sidecars reconcile \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-reconciliation.json \
  --verify-operator-chain \
  --fail-on-drift \
  --json
```

A green reconciliation requires matching sidecars and journal events, no digest drift, and a clean `operator_action_events` chain.

### Control-plane event projection index

After replay/reconciliation, operators can build a compact projection index that joins every
`*.event.json` sidecar to its durable `control-plane-event` journal entry:

```bash
strategy-validator-control-plane-event-sidecars index \
  --event-root docs/artifacts \
  --output-path scratch/control-plane-event-index.json \
  --fail-on-drift \
  --json
```

The index emits `control_plane_event_projection_index/v1` with per-event status,
source count, payload digest, and `fully_indexed` state. Treat `SIDECAR_ONLY`,
`JOURNAL_ONLY`, `DIGEST_MISMATCH`, or an unclean operator journal chain as drift
until explicitly waived.

### Semantic validator handoff contract ownership

Validator handoff packet and ingress-certificate contracts now live in
`strategy_validator/contracts/semantic_validator_handoff.py`. Legacy imports from
`strategy_validator.contracts.semantic` remain compatible, but new code should import
the stage-owned contracts directly. Submission/acceptance contracts remain in
`strategy_validator/contracts/semantic_validator_submission.py`.


### Operator action projection index

The operator-action journal now has a compact projection index command in the main ledger operations surface:

```bash
strategy-validator-ledger-ops index-operator-actions \
  --database-path /var/lib/strategy-validator/ledger.sqlite3 \
  --output-path scratch/operator-action-event-index.json \
  --json
```

Use this after `verify-operator-actions` when preparing control-plane event diagnostics. The index is a read model only; it does not mutate the ledger. It is intended to make journal-only events, control-plane event ids, payload digests, sequence linkage, and legacy/unchained records visible without reading raw SQLite rows.

### Semantic contract module ownership

The legacy `strategy_validator.contracts.semantic` module is now a compatibility facade. New code should import stage-owned semantic contracts from:

- `strategy_validator.contracts.semantic_core`
- `strategy_validator.contracts.semantic_feature_materialization`
- `strategy_validator.contracts.semantic_gate_artifact`
- `strategy_validator.contracts.semantic_adjudication_bundle`
- `strategy_validator.contracts.semantic_bundle_release_index`
- `strategy_validator.contracts.semantic_release_capsule`
- `strategy_validator.contracts.semantic_release_handoff`
- `strategy_validator.contracts.semantic_validator_handoff`
- `strategy_validator.contracts.semantic_validator_submission`

Legacy imports remain supported, but new stage work should not add classes back to `semantic.py`.

### Production smoke Markdown summaries

`production_smoke_check.py` can now emit a compact Markdown summary with `--summary-markdown-output-path`. Use this in CI artifact uploads so operators can review readiness, restore-drill, and operator-action journal status without opening the raw JSON payload first.


## Strategic horizon gate

Before treating later-horizon work as available, query `GET /readiness/strategic-horizon`
or call `strategy_validator.application.strategic_horizon_readiness.get_strategic_horizon_readiness_payload`.

A Horizon C capability is not considered live because it appears in a roadmap. It must
show concrete evidence in the readiness payload. In particular, provider automation
requires a credentialed burn-in artifact that proves live credentials, no fallback, and
freshness validation.

Release publication requests must supply an explicit `artifact_root`; policy, host
fingerprint, burn-in inputs, and publication output are rejected if they resolve outside
that root.

## Fast local preflight before release-candidate assessment

Before running a full release-candidate assessment, run the cheap gates first:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/environment_check.py --include-extra dev
PYTHONDONTWRITEBYTECODE=1 python -c "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"
```

`source_health.py` is intentionally side-effect free and checks the high-gravity
source files that historically carried syntax regressions. `environment_check.py`
validates the dependency envelope declared in `pyproject.toml`; notably, it must
report `pydantic>=2.6` before API/research/runtime tests are meaningful.

### Hygiene-safe repository health tooling

The repository health tools are now expected to be safe to run from a source
archive without creating bytecode caches:

```bash
python scripts/architecture_health_report.py > scratch/architecture-health.json
strategy-validator-release-candidate cleanup
PYTHONDONTWRITEBYTECODE=1 python -c "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"
```

`strategy-validator-release-candidate cleanup` removes `__pycache__/` directories
as well as `.pyc` files. `scripts/repository_truth_check.py` also verifies that
`.gitignore` and `.dockerignore` keep the same high-signal transient/runtime
artifact exclusions used by the hygiene gate.

### Command-policy compatibility seam

Legacy callers may still use
`strategy_validator.application.ui_command_actions.build_ui_operator_command_receipt_payload(...)`
when they need a direct journaled receipt in tests or non-route application code.
That helper is no longer a policy bypass: it now uses the same target-shape
policy as the token-aware API path and rejects targetless commands before the
operator-action journal is touched.

Idempotency keys are also payload-bound. Reusing the same key with the same
action/operator but a different governed target is rejected rather than silently
returning the previous receipt.

### Pyproject-derived environment gate

`python scripts/environment_check.py` derives runtime distribution requirements
from `[project].dependencies` in `pyproject.toml`. Do not update dependency
floors in a separate checklist; update packaging metadata first, then let the
environment gate enforce that truth in CI and release-candidate assessment.

### Dev dependency and source-archive manifest checks

For release-candidate assessment, use the dev dependency envelope because the
assessment path requires pytest and import-linter-backed checks:

```bash
python scripts/environment_check.py --include-extra dev
```

`strategy-validator-release-candidate assess` runs that dev-aware dependency gate
itself. When a release candidate is generated from a source archive rather than a
git checkout, the manifest fallback now excludes top-level `artifacts/`,
`scratch/`, cache directories, and bytecode files. Generated or debugging state
must not be sealed as release evidence simply because git metadata is absent.

### Clean full-repo handoff archive

Use the repo-native archive builder for full repository handoffs instead of
zipping the working directory directly:

```bash
python scripts/package_repo.py --output /tmp/strategy-validator-clean.zip
```

To plan removal of `__pycache__` directories and stray `.pyc` / `.pyo` files under
`strategy_validator/`, `tests/`, `scripts/`, `docs/`, and `configs/` (no other
trees), run `python scripts/purge_repo_transients.py --json`. That command is
dry-run only; pass `--apply` when you intend to delete those paths from the
worktree.

The archive builder includes source, tests, docs, workflows, scripts, configs,
and migrations while excluding generated `artifacts/`, `scratch/`, Python cache
folders, local virtual environments, dependency folders, and build outputs. A
dry-run health check is available with:

```bash
python scripts/package_repo.py --check
```

Release assessment now runs `scripts/environment_check.py --include-extra dev`
before pytest-backed checks. Dependency drift should therefore be reported as an
explicit environment-gate failure rather than an opaque pytest import failure.

### Clean handoff archive smoke

For full-repo handoffs, use the repo-native archive builder instead of manually zipping the
worktree:

```bash
python scripts/package_repo.py --check
python scripts/package_repo.py --output /tmp/strategy-validator-clean.zip --json
```

The archive builder filters generated release packets, scratch/debug output, bytecode caches,
virtual environments, dependency/build directories, and prior archive outputs (`.zip`, `.tar`,
`.gz`, `.tgz`). Written archives report `archive_sha256`; capture that digest in operator
handoffs when comparing artifacts across machines.

### Clean handoff archive verification

After building a full-repo handoff ZIP, verify it against the current source tree
before publishing or attaching it to an operator handoff:

```bash
python scripts/package_repo.py --check
python scripts/package_repo.py --output /tmp/strategy-validator-clean.zip --json
python scripts/verify_repo_archive.py /tmp/strategy-validator-clean.zip --json
```

`verify_repo_archive.py` checks that the archive contains exactly the clean file
selection, that ZIP metadata is normalized, and that each archived file digest
matches the source file. Treat verifier failure as a handoff blocker, not a
warning.

### Release bundle manifest verification

Release-candidate manifests are now membership-sealed. A generated
`bundle-manifest.json` uses `schema: 2` and includes `content_sha256`, a digest
of the normalized manifest entries. Run bundle verification after generation and
before handoff:

```bash
strategy-validator-release-candidate generate --candidate rc-local
strategy-validator-release-candidate verify-bundle --candidate rc-local
```

Verification fails if the manifest omits a current source/config/test/doc file,
contains stale or duplicate paths, has malformed path records, or if any file
size/SHA-256 differs from the current worktree. Treat `bundle-verify.json` with
`ok: false` as a release blocker.

### SQLite migration truth gate

Before release assessment or handoff publication, run the migration truth gate:

```bash
python scripts/migration_truth_check.py
```

This check applies all SQLite migrations twice to an in-memory database and
verifies the expected schema version, required ledger/operator-action tables, and
required operator-action indexes. It does not touch the configured production
ledger path. Treat failure as a release blocker because it means the migration
chain is not idempotent or no longer produces the expected schema shape.

Recommended fast local preflight is now:

```bash
PYTHONDONTWRITEBYTECODE=1 python scripts/source_health.py
python scripts/repository_truth_check.py
python scripts/migration_truth_check.py
python scripts/package_repo.py --check
python scripts/environment_check.py --include-extra dev
PYTHONDONTWRITEBYTECODE=1 python -c "from strategy_validator.cli.hygiene_check import main; raise SystemExit(main([]))"
```

### Release assessment bundle gate

`strategy-validator-release-candidate assess` now verifies the candidate bundle
manifest before running readiness checks. The first assessment check is
`bundle-verify`; if the manifest omits a current source/config/test/doc file,
contains stale paths, or has a mismatched `content_sha256`, assessment fails
immediately and writes an assessment record with `schema: 2`.

The preferred local sequence remains:

```bash
strategy-validator-release-candidate generate --candidate rc-local
strategy-validator-release-candidate assess --candidate rc-local --skip-frontend
strategy-validator-release-candidate verify-bundle --candidate rc-local
```

The explicit `verify-bundle` command is still useful as a standalone handoff
check, but assessment itself now enforces the same bundle-membership guard.

### SQLite migration contract depth

`python scripts/migration_truth_check.py` now reports `migration_truth_check/v2`.
In addition to schema version, idempotency, tables, and indexes, it verifies the
required column contract and proves SQLite rejects duplicate non-empty operator
action idempotency keys. This is a release blocker because operator command
replay safety depends on the database-level uniqueness constraint, not only on
application-side lookup logic.

### Runtime-state-safe repository handoff

The clean repository archive tooling is now also a runtime-state filter. Before
sharing or sealing a full-repo handoff, use:

```bash
python scripts/package_repo.py --check
python scripts/package_repo.py --output /tmp/strategy-validator-clean.zip --json
python scripts/verify_repo_archive.py /tmp/strategy-validator-clean.zip --json
```

The archive selector prunes generated directories during traversal and excludes
prior archive outputs, bytecode/cache directories, local SQLite databases,
SQLite WAL/SHM files, logs, and JSONL event streams. The verifier checks exact
membership, sorted entries, fixed timestamps, normalized file permissions, ZIP
compression mode, and source/archive digest parity. Treat verifier failure as a
handoff blocker.

### Clean archive output-path safety

`python scripts/package_repo.py` now refuses to write an archive output under the
repository root if that output path would itself be selected as source content on
the next archive build. Use one of these safe patterns:

```bash
python scripts/package_repo.py --output /tmp/strategy-validator-clean.zip --json
python scripts/package_repo.py --output ./strategy-validator-clean.zip --json
```

The first writes outside the repo. The second is safe because `.zip` is an
explicitly excluded suffix. Avoid repo-local non-archive names such as
`./handoff.bin`; the tool treats those as future archive members and fails
closed.

## Release manifest header verification

`strategy-validator-release-candidate verify-bundle` validates more than file
hashes. The release manifest must be schema `2`, its `entry_count` must match the
number of listed entries, and `content_sha256` must be a 64-character hexadecimal
digest matching the normalized `(path, size_bytes, sha256)` membership set.

Treat any non-empty `manifest_errors` list in `bundle-verify.json` as a release
blocker. Manifest-header failures indicate malformed or stale release evidence;
do not continue with assessment or handoff until a fresh candidate packet is
generated and verified.

## Malformed release-manifest digest entries

`strategy-validator-release-candidate verify-bundle` now treats malformed digest
entry fields as controlled release evidence failures.  If a manifest entry has a
non-integer or negative `size_bytes`, a non-hexadecimal SHA-256 digest, or another
field that prevents `content_sha256` recomputation, the verifier writes
`bundle-verify.json` with `ok: false`, records the malformed entry, and adds a
`content_sha256 cannot be recomputed` manifest error.  Operators should treat
that exactly like a file-hash mismatch: the candidate is not releasable until a
fresh candidate bundle is generated and verified.

### Release bundle malformed-manifest handling

`strategy-validator-release-candidate verify-bundle` is fail-closed for malformed
bundle manifest containers. If `bundle-manifest.json` is invalid JSON, not a JSON
object, or has a non-list `entries` field, the verifier writes
`bundle-verify.json` with `ok: false`, `manifest_error_count > 0`, and a concrete
`manifest_errors` reason.

Treat these failures as release blockers. Do not manually edit the manifest to
recover a candidate; regenerate the release candidate packet and rerun the full
preflight chain.

### Release bundle non-regular path handling

`strategy-validator-release-candidate verify-bundle` also fails closed when a
manifest entry points at a non-regular path, such as a directory, or a path that
cannot be read. The verifier writes `bundle-verify.json` with `ok: false` and a
`malformed` entry rather than crashing during SHA-256 calculation.

Treat this as release-evidence corruption. Regenerate the candidate packet from a
clean source tree and rerun the full release preflight chain.

### Release candidate id safety

Release-candidate ids are artifact path segments and are now validated before any
candidate directory is created or read. Use simple ids such as:

```bash
strategy-validator-release-candidate generate --candidate rc-2026-04-29-a
```

Do not use path-like ids such as `../rc`, `nested/rc`, or `nested\\rc`; the tool
rejects those before resolving artifact paths. This prevents release evidence
from being written outside `artifacts/release_candidate/`.

### Symlink-safe release and handoff evidence

Clean handoff ZIPs and release-candidate manifests must contain regular source
files only. Symbolic links are excluded from `scripts/package_repo.py` archive
selection, and `strategy-validator-release-candidate generate` rejects tracked
symlink paths before writing a bundle manifest.

If `verify-bundle` reports a manifest path as `is a symbolic link`, treat the
candidate as corrupted release evidence. Remove the symlink or replace it with a
regular source file, then regenerate and verify the release candidate packet.

### Release manifest path canonicalization

Release-candidate manifests are regular-source-file evidence only. If `verify-bundle` reports a malformed path such as `./file`, `a//b`, `a/./b`, `a\\b`, an absolute path, or a traversal segment, regenerate the release candidate packet. Do not manually normalize the manifest: the candidate packet must be generated by the repo tooling so path identity, file hashes, and `content_sha256` remain aligned.

### Sorted release manifest entries

Release-candidate bundle manifests must keep entries sorted by canonical
repo-relative POSIX path. If `verify-bundle` reports `entries must be sorted by
canonical path`, treat the candidate as manually modified or stale release
evidence. Regenerate the candidate packet instead of reordering the manifest by
hand.
