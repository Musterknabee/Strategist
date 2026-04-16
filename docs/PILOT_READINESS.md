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

For a **local controlled** HTTP JSON burn-in (no Alpaca keys), from repo root:

```text
python scripts/pilot_http_burnin_driver.py 60
```

Writes `pilot_burnin_round{1,2}.jsonl` and `pilot_burnin_round*_analyze.txt` (gitignored); pass rounds `30`–`100` as the optional argument. See `docs/PILOT_BURNIN_REPORT.md` for a sample outcome.

**Staging then Alpaca** (two-phase, `--resolution`): `python scripts/pilot_staging_alpaca_burnin_driver.py 60`

**Follow-up Alpaca-only** (longer pass, off-hours hint, second symbol): `python scripts/pilot_followup_burnin_driver.py --help`

## Tune policy from observations only

```text
python -m strategy_validator.cli.pilot analyze pilot_liquidity.jsonl
```

The second section prints **commented** `STRATEGY_VALIDATOR_*` suggestions derived
only from aggregate counts in the file (rate-limit proxy, stale age, auth, 5xx,
latency p95). Operators paste into config after review — not applied automatically.

## Milestone status

Pilot burn-in milestone is marked complete in documentation with continuous,
append-only evidence in `docs/PILOT_BURNIN_REPORT.md`.

- Milestone label: `PILOT_BURNIN_COMPLETE`
- Artifact archive bundle: `docs/artifacts/pilot_burnin_complete_20260413T080723Z`
- Run/env/policy fingerprint: `docs/artifacts/pilot_burnin_complete_20260413T080723Z/RUN_FINGERPRINT.json`

## Controlled operational rollout

Move from engineering validation to controlled operations under these rules:

1. Keep interface freeze and policy threshold values unchanged unless a new
   run artifact shows a concrete defect that requires adjustment.
2. Run canary-style operational checks on a fixed symbol set and capture
   `pilot analyze` outputs as append-only evidence in the burn-in report.
3. Escalate to RC2 only when evidence demonstrates a required runtime policy
   or behavior correction; do not cut RC2 for a clean pilot.

Typed operational artifacts for this phase:

- Host fingerprint: `python -m strategy_validator.cli.rollout_ops fingerprint --host-kind KEYED_OPERATOR_HOST --output docs/artifacts/keyed_host_fingerprint.json`
- Rollout bundle: `python -m strategy_validator.cli.rollout_ops bundle ... --output docs/artifacts/controlled_rollout_bundle.json`
- Daily checklist: `python -m strategy_validator.cli.rollout_ops daily-checklist ... --output docs/artifacts/daily_checklist.json`
- Release decision: `python -m strategy_validator.cli.rollout_ops review docs/artifacts/daily_checklist.json --output docs/artifacts/release_decision.json`
