# Optional research and data APIs

The backend **does not require** third-party market data, news, macro, filings, crypto, sports, or broker API keys to start. All connectors are **opt-in**.

Secrets belong only in **gitignored** files (`deployment.env`, `.env.local`, `.keys/`). Never commit real keys, never log full keys, and never put provider secrets in `NEXT_PUBLIC_*` frontend variables.

## Machine-readable registry

- **Module:** `strategy_validator.contracts.provider_capabilities`
- **CLI:** `strategy-validator-provider-capabilities --json`
- **Schema:** `provider_capabilities/v2` (`schema_version` in JSON output)

Each `ProviderCapability` row includes: `provider_id`, `display_name`, `category`, `access_type`, `env_vars`, `requires_secret`, `official_docs_url`, `signup_url`, `research_role`, `may_gate_live_promotion`, `default_trust_level`, `pit_suitability`, rate/license notes, and `recommended_priority` (lower = higher suggested priority for wiring).

### Trust and PIT hints

| `default_trust_level` | Typical meaning |
| --- | --- |
| `OFFICIAL_SOURCE` | Government or primary statistical authority |
| `LICENSED_PROVIDER` | Contractual / registered access |
| `FREEMIUM_RESEARCH_ONLY` | Aggregator; research posture unless licensed |
| `PUBLIC_BEST_EFFORT` | Public API without signup |
| `BROKER_EXECUTION` | Execution / broker surface (not canonical macro PIT) |
| `UNAVAILABLE` | Placeholder / not wired |

| `pit_suitability` | Meaning |
| --- | --- |
| `STRONG_PIT_SOURCE` | Strong revision discipline; still timestamp-aware |
| `PIT_WITH_RELEASE_TIMESTAMP` | Use release / observation timestamps explicitly |
| `BEST_EFFORT_AS_OF` | Point-in-time claims need extra evidence |
| `NOT_PIT_SAFE_WITHOUT_ARCHIVE` | Snapshots / news; archive for rigor |
| `EXECUTION_ONLY` | Broker quotes; not macro PIT authority |

## Public / no-signup providers

| Provider | `provider_id` | Notes |
| --- | --- | --- |
| SEC EDGAR | `sec_edgar` | Set descriptive `SEC_USER_AGENT` (recommended) |
| World Bank indicators | `world_bank_open_data` | |
| ECB SDW | `ecb` | |
| Eurostat | `eurostat` | |
| OECD | `oecd` | |
| IMF Data | `imf_data` | |
| BLS v1 | `bls` | Unregistered public API |
| GDELT | `gdelt` | |
| Binance public | `binance_public` | |
| Kraken public | `kraken_public` | |

## Signup / API-key providers (optional)

| Provider | `provider_id` | Env vars (see `.env.example`) |
| --- | --- | --- |
| FRED | `fred` | `FRED_API_KEY` |
| BLS v2 | `bls_registered_api` | `BLS_API_KEY` |
| Alpha Vantage | `alpha_vantage` | `ALPHA_VANTAGE_API_KEY` (alias `ALPHAVANTAGE_API_KEY`) |
| Finnhub | `finnhub` | `FINNHUB_API_KEY` |
| FMP | `financial_modeling_prep` | `FMP_API_KEY` |
| Twelve Data | `twelve_data` | `TWELVE_DATA_API_KEY` |
| Tiingo | `tiingo` | `TIINGO_API_KEY` |
| EODHD | `eodhd` | `EODHD_API_KEY` |
| Nasdaq Data Link | `nasdaq_data_link` | `NASDAQ_DATA_LINK_API_KEY` |
| Polygon.io | `polygon_io` | `POLYGON_API_KEY` |
| Massive | `massive` | `MASSIVE_API_KEY`, `POLYGON_API_KEY` |
| Guardian | `guardian_open_platform` | `GUARDIAN_API_KEY` |
| NewsAPI | `newsapi` | `NEWSAPI_KEY`, `NEWSAPI_API_KEY` |
| Mediastack | `mediastack` | `MEDIASTACK_API_KEY` |
| CoinGecko | `coingecko` | `COINGECKO_API_KEY` (optional on free tier) |
| CoinMarketCap | `coinmarketcap` | `COINMARKETCAP_API_KEY` |
| The Odds API | `the_odds_api` | `THE_ODDS_API_KEY` |
| football-data.org | `football_data_org` | `FOOTBALL_DATA_API_KEY`, `FOOTBALL_DATA_API_TOKEN` |
| API-Football / API-Sports | `api_sports` | `API_SPORTS_KEY`, `API_FOOTBALL_KEY`, `APISPORTS_KEY` |
| Sportmonks | `sportmonks` | `SPORTMONKS_API_KEY`, `SPORTMONKS_API_TOKEN` |

Freemium market-data rows default `may_gate_live_promotion=false` in the registry (research-only posture unless you extend policy elsewhere with licensing).

## Broker: Alpaca (paper-first)

- **Registry:** `alpaca`, `access_type=BROKER_ACCOUNT_REQUIRED`, `pit_suitability=EXECUTION_ONLY`.
- **Defaults:** `ALPACA_BASE_URL=https://paper-api.alpaca.markets`, `ALPACA_TRADING_MODE=paper`, `PERSONAL_LIVE_APPROVED=false`.
- **Live guard:** tooling treats `ALPACA_TRADING_MODE=live` or a live trading base URL as a **policy violation** unless `PERSONAL_LIVE_APPROVED=true` or `STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED=true`.
- **KYC / live money:** complete outside this repo; do not use this documentation as trading advice.

Registry field `personal_live_trading_env_gate` is `PERSONAL_LIVE_APPROVED` (legacy alias above still honored in scripts).

## Environment templates

- **Placeholders:** `deployment.env.sample`, `.env.example`
- **Real values:** `deployment.env`, `.env.local`, or `.keys/` (all gitignored)

## Sample retrieval

Public providers (small samples, rate-limit friendly):

```bash
python scripts/retrieve_provider_samples.py --public-only --output-dir artifacts/provider_samples --manifest-json
```

Offline / CI-safe stubs:

```bash
python scripts/retrieve_provider_samples.py --public-only --no-network --output-dir artifacts/provider_samples --manifest-json
```

Keyed providers (skipped when keys missing; never fails the run):

```bash
python scripts/retrieve_provider_samples.py --configured-keyed-only --env-file deployment.env --output-dir artifacts/provider_samples --manifest-json
```

Explicit subset (aliases: `sec`, `world_bank`, `imf`, `binance`, `kraken`):

```bash
python scripts/retrieve_provider_samples.py --providers sec,fred --env-file deployment.env --output-dir artifacts/provider_samples --manifest-json
```

Artifacts default under `artifacts/` (gitignored). Do not commit raw provider responses unless repo policy explicitly allows generated data.

### Sample manifest fields (`provider_samples_manifest/v1`)

Each entry is sorted by `provider_id`. Besides transport `status` (`OK`, `HTTP_*`, …), entries include:

| Field | Meaning |
| --- | --- |
| `classified_status` | `OK`, `NON_JSON_BUT_VALID`, `RATE_LIMITED`, `TEMPORARILY_UNAVAILABLE`, `ENDPOINT_CHANGED`, `NETWORK_BLOCKED`, `PARSE_ERROR`, `AUTH_FAILED`, `PLAN_LIMITED`, or stub values (`SKIPPED_NO_NETWORK`, `PENDING_KEY`, `PENDING_MANUAL_BROKER_SETUP`, `POLICY_SKIP`, …) |
| `http_status` | HTTP status, or `-1` / `-2` (client/stub) |
| `normalized_metadata` | Sorted hints: `detected_format`, `byte_length`, optional XML/CSV previews (no secrets) |

GDELT may return `RATE_LIMITED` on busy networks; the script waits briefly and retries **once** before giving up.

## Key validation (redacted)

```bash
python scripts/check_provider_keys.py --env-file deployment.env --json
```

Reports `configured` / `matched_env_var` and **SHA-256 prefix only** (16 hex chars) for fingerprints—never full secrets. Exits non-zero if Alpaca live mode is configured without personal approval.

## Human signup checklist

For each key provider you need:

1. Open `signup_url` / `official_docs_url` from `strategy-validator-provider-capabilities --json`.
2. Choose the **free** tier only; do not accept paid obligations.
3. Create keys in a **dedicated** account or alias when possible.
4. Paste keys only into **gitignored** env files (never docs, tests, or frontend public env).
5. Re-run `check_provider_keys.py` and optionally `retrieve_provider_samples.py --configured-keyed-only`.

If signup requires email verification, CAPTCHA, 2FA, phone, payment, or identity checks, complete those steps manually and resume afterward.

## Provider priority order

Use `recommended_priority` from the registry JSON (ascending: **lower number = wire first** for research breadth). Official macro and filings sources are typically prioritized before freemium aggregators.

## Commands reference

```bash
python -m compileall -q strategy_validator scripts tests
python scripts/source_health.py --json
python scripts/repository_truth_check.py --json
python -m pytest -q --tb=short
strategy-validator-provider-capabilities --json
```

On **Windows**, run pytest **directly** and rely on **pytest’s exit code** (or `python scripts/ci_local_verify.py`). Do **not** pipe pytest into `findstr "FAILED"`: `findstr` returns exit code 1 when there are no matches, which can falsely fail an all-green run. See [WINDOWS_PYTEST_VERIFICATION.md](../development/WINDOWS_PYTEST_VERIFICATION.md).
