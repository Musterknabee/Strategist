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
