# Daily paper tracking (scheduled CLI)

**Scope:** Deterministic batch evaluation over enrolled paper manifests. **No broker orders** from this path.

## CLI

```bash
strategy-validator-paper-track run-daily \
  --tracking-root artifacts/paper_tracking \
  --date 2026-05-01 \
  --json
```

Produces `artifacts/paper_tracking/daily_runs/{date}/daily_run_manifest.json`.

## Scheduling

Use Windows Task Scheduler, `cron`, `systemd` timers, or a Docker host wrapper to invoke the CLI once per day. The API does not run background schedulers.

## Read-plane / UI

Latest daily manifest is surfaced on paper tracking payloads when present.

## Limitations

Failures on individual candidates are recorded; the run continues. No live network unless you separately configure provider ingestion.

## Next graduation step

Archive daily manifests with your evidence retention policy; link digests in operator runbooks.
