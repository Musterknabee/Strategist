# Provider-backed paper research loop

This document describes the **governed provider snapshot → gauntlet → paper tracking → broker policy evidence** path. It is **not** live trading, **not** browser order execution, and **not** a profitability or production-readiness certification.

## What you get

- **Provider historical snapshots** as digest-linked manifests (`provider_historical_snapshot_manifest/v1`, `provider_historical_snapshot_run/v1`).
- **Strategy batch** specs can declare `data_source.kind: "provider_snapshot"` pointing at a manifest on disk (batch runner performs **no live provider calls**).
- **`provider_paper_loop_manifest/v1`** ties ingestion, gauntlet, paper tracking, promotion packet, optional portfolio sim, and **paper broker status artifact** together under `STRATEGY_VALIDATOR_ARTIFACT_ROOT`.
- **Read-plane** surfaces: `GET /ui/research-os/status` (extended payload), Strategist Terminal pages `/research-os`, `/providers`, `/strategy-lab`, `/paper-tracking`.

## Safety boundaries

- No live trading; Alpaca integration remains **paper-first**; live endpoints / modes are **BLOCKED_BY_POLICY** in broker policy evaluation.
- No broker orders from the browser; CLI may expose paper order tools separately — not used by this loop.
- No API tokens in `NEXT_PUBLIC_*`; consolidated status never prints raw env secrets.
- **Normal pytest** does not hit the live network; use `--fixture` / packaged CSV manifests for deterministic runs.

## Artifact layout (under `STRATEGY_VALIDATOR_ARTIFACT_ROOT`)

| Path | Purpose |
|------|---------|
| `provider_historical_snapshots/latest/provider_historical_snapshot_run.json` | Snapshot run aggregate |
| `strategy_runs/...` | Gauntlet / batch outputs |
| `paper_tracking/...` | Enrolled candidates, scorecards, lifecycle |
| `paper_broker/latest/paper_broker_status.json` | Policy / optional account summary (redacted) |
| `provider_paper_loop/latest/provider_paper_loop_manifest.json` | End-to-end loop manifest |

## CLI entrypoints

### Ingest (multi-symbol, offline by default)

```bash
strategy-validator-provider-bars ingest \
  --provider tiingo \
  --symbol SPY --symbol QQQ \
  --timeframe 1d \
  --start 2024-01-02 --end 2024-06-30 \
  --as-of 2024-06-30T16:00:00Z \
  --output-root artifacts/provider_historical_snapshots \
  --env-file deployment.env \
  --json
```

- Default posture is **offline** (no HTTP) unless you pass **`--allow-network`** and configured keys exist.
- **`--fixture path/to/manifest.json`** embeds a packaged snapshot (used in tests / demos).

Legacy single-symbol mode is still available as the first positional form is rewritten to `legacy-ingest`:

```bash
strategy-validator-provider-bars legacy-ingest --provider tiingo --symbol SPY ...
```

### Paper broker status artifact

```bash
strategy-validator-paper-broker status \
  --output-root artifacts/paper_broker \
  --json
```

Add **`--allow-network`** only on a trusted host when you want an account probe after policy reports `PAPER_READY`.

### Full loop (fixture-first)

From repo root (uses packaged `tests/fixtures/provider_snapshots/` by default):

```bash
python scripts/run_provider_paper_loop.py \
  --artifact-root artifacts \
  --run-id provider-paper-demo \
  --overwrite \
  --json
```

Or:

```bash
strategy-validator-provider-paper-loop --artifact-root artifacts --run-id demo --overwrite --json
```

## Docker alignment

Run the loop **inside** the API container if you want paths to match the process exactly:

```powershell
docker exec strategist-local-api strategy-validator-provider-paper-loop `
  --artifact-root /var/lib/strategy-validator/artifacts `
  --run-id docker-provider-demo `
  --overwrite `
  --json
```

Then `GET http://127.0.0.1:8000/ui/research-os/status` should show `provider_paper_loop_latest` and related fields without mounting surprises.

## Troubleshooting

| Symptom | Meaning |
|---------|---------|
| `PENDING_KEY` / `NO_NETWORK_WITHOUT_FIXTURE` | Expected when offline without a fixture manifest. |
| `PROVIDER_BARS_SHA256_MISMATCH` | Bars file changed after manifest was written; regenerate manifest or restore CSV. |
| `PIT_STRICT_REJECTS_BEST_EFFORT_PROVIDER_SNAPSHOT` | Batch `pit_policy: STRICT` rejects `BEST_EFFORT_AS_OF` provider PIT. |
| `NO_PROVIDER_PAPER_LOOP_ARTIFACT` on `/ui/research-os/status` | Loop manifest not yet written under the artifact root the API uses. |

## Related docs

- [RESEARCH_OPERATING_SYSTEM.md](./RESEARCH_OPERATING_SYSTEM.md)
- [PROVIDER_HISTORICAL_DATA.md](./PROVIDER_HISTORICAL_DATA.md)
- [PAPER_BROKER_ALPACA.md](./PAPER_BROKER_ALPACA.md)
- [OPTIONAL_RESEARCH_DATA_APIS.md](../providers/OPTIONAL_RESEARCH_DATA_APIS.md)
