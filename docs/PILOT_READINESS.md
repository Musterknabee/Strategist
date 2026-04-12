# Pilot readiness (RC `0.1.0rc1`)

## Frozen interface surface

Runtime JSON contracts and policy seams are pinned for this RC via
`strategy_validator.contracts.interface_freeze` (`PILOT_RC_INTERFACE_FREEZE`,
`FROZEN_IMPORT_SURFACE`). CI imports that module to guard against accidental
removals.

## Release candidate tag

With git available from the repo root:

```text
git tag -a v0.1.0-rc.1 -m "strategy-validator 0.1.0rc1 pilot interface freeze"
```

Package version is `0.1.0rc1` (PEP 440); the git tag uses hyphenated form for readability.

## Controlled real-provider run

1. Copy `deployment.env.sample` into a **non-production** secrets store; set one connector:
   - Alpaca: `STRATEGY_VALIDATOR_ALPACA_MARKET_DATA_ENABLED=True` and keys, **or**
   - HTTP JSON: templates pointing at a **staging** feed you control.
2. Set optional `PILOT_PROBE_SYMBOL` (default `SPY`).
3. Collect lines:

```text
python -m strategy_validator.cli.pilot probe --rounds 20 --output pilot_liquidity.jsonl
```

Each line is NDJSON (`pilot_schema: 1`) with latency, provider status, circuit state,
typed `failure_domain` / `failure_code`, and LIVE snapshot age when present.

## Tune policy from observations only

```text
python -m strategy_validator.cli.pilot analyze pilot_liquidity.jsonl
```

The second section prints **commented** `STRATEGY_VALIDATOR_*` suggestions derived
only from aggregate counts in the file (rate-limit proxy, stale age, auth, 5xx,
latency p95). Operators paste into config after review — not applied automatically.
