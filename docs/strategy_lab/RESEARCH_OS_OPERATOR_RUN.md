# Research OS Operator Run

The Research OS operator run is a paper-only orchestration artifact. It sequences the existing evidence spine:

```text
closure manifest
→ closure verification
→ operator attestation
→ briefing pack
→ portable export bundle
→ operator run manifest
```

It does **not** authorize live trading, broker orders, deployment approval, or profitability claims.

## Command

```bash
strategy-validator-research-os-run run \
  --run-id daily-research-run \
  --operator-id local-operator \
  --overwrite \
  --json
```

Host helper:

```bash
python scripts/run_research_os_operator_run_demo.py \
  --artifact-root artifacts \
  --run-id research-os-operator-run-demo \
  --overwrite \
  --json
```

## Artifacts

```text
artifacts/research_os_operator_runs/
  runs/{run_id}/research_os_operator_run_manifest.json
  latest/research_os_operator_run_manifest.json
  latest/latest_ref.json
```

The manifest records each step, status, artifact path, artifact digest, warnings, blockers, and the final `operator_run_spine_sha256`.

## Read-plane

```text
GET /ui/research-os/run/latest
GET /ui/research-os/status  # includes research_os_operator_run_latest
```

Frontend page:

```text
/research-run
```

## Status interpretation

- `COMPLETE`: all steps completed without warnings/blockers.
- `RESTRICTED`: evidence was produced, but missing optional artifacts, degraded subsystem status, or warnings remain.
- `BLOCKED`: a step had a blocker or a terminal verification/export failure.
- `EMPTY`: no operator-run steps were available.

`RESTRICTED` is expected in fixture/demo mode when optional provider, broker, or strategy batch artifacts are absent.

## Safety rules

- No live trading.
- No broker orders.
- No browser order controls.
- No ledger writer authority.
- No `DEPLOYMENT_APPROVED` change.
- No profitability certification.
