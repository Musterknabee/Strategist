# Deployment Runbook

## Single-node deployment surface

This repository's v1 production target is a single service deployment with:

- `strategy-validator-api` as the only long-running process
- `strategy-validator-migrate` as the explicit schema upgrade step
- one append-only SQLite ledger mounted outside the container image
- one operator-managed env file or secrets store derived from `deployment.env.sample`

The checked-in local manifest is:

- `docker-compose.yml`

It binds the FastAPI service on port `8000` and mounts the runtime ledger/artifact directory at:

- `/var/lib/strategy-validator`

## Bring-up

1. Copy `deployment.env.sample` into a deployment-specific env file or secrets store.
2. Set `STRATEGY_VALIDATOR_MODE=PRODUCTION`.
3. Set `STRATEGY_VALIDATOR_API_TOKEN` and the sanctioned provider credentials.
4. Keep `STRATEGY_VALIDATOR_LEDGER_DB_PATH` on the mounted runtime volume.
5. Run the explicit schema migration before first boot or after upgrading the image:

```text
docker compose run --rm strategy-validator strategy-validator-migrate --database-path /var/lib/strategy-validator/forensic_ledger.sqlite3 --json
```

6. Start the API:

```text
docker compose up -d strategy-validator
```

7. Verify transport and truthful readiness:

```text
curl http://127.0.0.1:8000/healthz
curl http://127.0.0.1:8000/readyz
```

## Backup drill

Treat the mounted ledger and runtime artifacts as the recovery boundary.

Before image replacement or schema upgrade:

1. Stop write traffic or place the node in operator maintenance.
2. Copy the mounted runtime directory to a timestamped backup path.
3. Record the image tag, git revision, and backup location in the operator handoff log.

Example:

```text
cp -R artifacts/runtime artifacts/backups/runtime-2026-04-16T184500Z
```

Minimum backup contents:

- `forensic_ledger.sqlite3`
- release closure artifacts needed for current signoff
- operator command event logs if present under the mounted runtime root

## Rollback drill

Rollback is operator-governed and must remain fail-closed.

1. Stop the current container:

```text
docker compose stop strategy-validator
```

2. Restore the last known-good runtime backup over the mounted runtime directory.
3. Re-run migration against the restored ledger to confirm schema compatibility:

```text
docker compose run --rm strategy-validator strategy-validator-migrate --database-path /var/lib/strategy-validator/forensic_ledger.sqlite3 --json
```

4. Restart the service on the last known-good image or worktree.
5. Re-check `/healthz` and `/readyz`.
6. Re-derive release posture from the current closure snapshot before resuming governed operator activity.

## Non-goals

This runbook does not introduce:

- multi-node orchestration
- distributed workers
- automated rollback controllers
- storage engine changes beyond the existing SQLite ledger
