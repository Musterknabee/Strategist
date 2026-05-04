# Backend container v1

This deployment envelope packages only the Python `strategy-validator` backend API. It does **not** include a frontend, worker fleet, or multi-tenant runtime.

## Runtime contract

The container defaults to production mode and starts with:

```bash
strategy-validator-api --host 0.0.0.0 --port 8000
```

Required production environment:

| Variable | Required | Purpose |
|---|---:|---|
| `STRATEGY_VALIDATOR_MODE=PRODUCTION` | yes | Enables fail-closed production startup checks. |
| `STRATEGY_VALIDATOR_API_TOKEN` | yes | Protects mutation-capable API routes. The image deliberately does not set a token. Use a unique high-entropy value, not a placeholder. |
| `STRATEGY_VALIDATOR_API_TOKEN_SCOPES` | yes | Must include `operator:command:write,operator:projection:read`; production rejects missing scopes. |
| `STRATEGY_VALIDATOR_LEDGER_DB_PATH` | yes | Absolute path to the SQLite evidence ledger. Defaults to `/var/lib/strategy-validator/ledger.sqlite3`. |
| `STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR` | strongly recommended | Writable backup target used by deployment readiness checks. Defaults to `/var/backups/strategy-validator`. |
| `STRATEGY_VALIDATOR_ARTIFACT_ROOT` | strongly recommended | Mounted writable artifact/publication root for release and operator evidence outputs. Defaults to `/var/lib/strategy-validator/artifacts`. |
| `STRATEGY_VALIDATOR_HOST_PORT` | optional | Loopback host port used by generated Docker Compose/systemd templates and smoke target derivation. Defaults to `8000`; must be numeric and within `1..65535`. |

## Build

```bash
docker build -t strategy-validator-api:local .
```

## Local production smoke run

```bash
docker run --rm \
  -p 8000:8000 \
  -e STRATEGY_VALIDATOR_MODE=PRODUCTION \
  -e STRATEGY_VALIDATOR_API_TOKEN='<real-random-token-at-least-32-chars>' \
  -e STRATEGY_VALIDATOR_API_TOKEN_SCOPES=operator:command:write,operator:projection:read \
  -e STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3 \
  -e STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator \
  -e STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  strategy-validator-api:local
```

The process intentionally refuses to bind in production if runtime readiness is blocked. Use `strategy-validator-single-tenant-preflight --prepare --verify-backup-restore --require-ready` against the mounted volumes before promotion when deployment readiness requires a migrated ledger database and writable backup/artifact paths.

For target-host templates, prefer the generated single-tenant bundle. Its Docker Compose and systemd templates run the non-root image with a read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, and a tmpfs `/tmp`. Before stale-container cleanup or long-lived API startup, the systemd template runs `strategy-validator-deployment-env-check /deployment-env/deployment.env --require-valid --json` inside a short-lived hardened container, so malformed tokens, scopes, paths, or host ports fail with a clear env-check report before Docker receives a bad port bind and before an existing API container is removed. The systemd template still ignores stale-container cleanup failures and stop-time already-stopped failures, which keeps first boot and shutdown idempotent while the actual `docker run` command remains fail-closed. Both templates use `STRATEGY_VALIDATOR_HOST_PORT` for the loopback host bind, so systemd and Compose stay aligned with API smoke target derivation when the operator chooses a non-default port. For Compose deployments, use the generated `commands/compose-up.sh` helper; Docker Compose does not use the service `env_file:` stanza as an interpolation source for `ports:`, and the helper canonicalizes custom env/Compose paths before exporting `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` so the API container runtime `env_file` matches the same validated absolute env file used for interpolation. The generated bundle checker also validates expected Docker hardening flag counts for Compose, systemd, and helper scripts, which blocks regenerated bundles that accidentally duplicate or drop read-only, tmpfs, capability-drop, or no-new-privileges safeguards. Post-deploy evidence Docker fallbacks keep `/bundle`, `/repo`, and `/env` read-only and mount only `/evidence` as read-write. The generated evidence helper canonicalizes custom bundle/repo/env/evidence paths before local CLI or Docker fallback execution, keeping final evidence reads and writes aligned even when an operator supplies relative overrides.

## API smoke target URL

The packaged `strategy-validator-single-tenant-api-smoke` command and generated `commands/api-smoke.sh` derive their target URL from `STRATEGY_VALIDATOR_BASE_URL` when set, otherwise from `STRATEGY_VALIDATOR_HOST_PORT` in the environment or deployment env file, and finally default to `http://127.0.0.1:8000`. This keeps the smoke path aligned with the generated Compose binding `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000` and the generated systemd binding `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000`.

## Probes

The API registers:

- `/healthz` for container liveness
- `/livez` for process liveness
- `/readyz` for runtime readiness

`/readyz` returns HTTP 503 when runtime readiness is not `READY`.

## Scope boundary

This is a backend-only envelope. It is suitable for single-tenant operator validation and smoke deployment, not for frontend hosting, distributed workers, or multi-tenant exposure.

## Backup and restore smoke path

Before replacing a production ledger volume, verify the source backup and restore into a fresh destination path:

```bash
python -m strategy_validator.cli.ledger_ops restore \
  --backup-path /var/backups/strategy-validator/forensic_ledger_YYYYMMDDTHHMMSSZ.sqlite3 \
  --database-path /var/lib/strategy-validator/restored-ledger.sqlite3 \
  --json
```

The restore command refuses to overwrite an existing destination unless `--allow-overwrite` is supplied. When overwrite is allowed, `ledger_ops restore` preserves the displaced destination ledger first and reports `ledger_ops_pre_restore_backup/v1` with its path, size, and SHA-256. Treat overwrite restore as a break-glass operation: stop the API process first, set a durable `--pre-restore-backup-dir`, keep the restore JSON as evidence, then run `ledger_ops verify-integrity` against the restored file before reopening the service.



## Slice 21: event journal bridge and sidecar replay

Control-plane event sidecars can now be replayed with `build_control_plane_event_sidecar_replay_report(...)` and materialized as a projection artifact with `write_control_plane_event_sidecar_replay_report(...)`. Event-backed materializers may opt in to durable operator journal recording via `append_to_operator_journal=True`; this writes the verified event envelope to `operator_action_events` as a `control-plane-event` action while preserving the `.event.json` sidecar as a filesystem rendering.

The production smoke script also accepts `--restore-drill-backup-path` plus `--restore-drill-database-path` for a verified restore drill that can be paired with readiness checks.

## Single-tenant preflight gate

Before exposing the backend container, run the single-tenant preflight command against the same mounted volumes and secret environment that the API will use:

```bash
strategy-validator-single-tenant-preflight \
  --prepare \
  --verify-backup-restore \
  --require-ready \
  --json
```

This gate verifies production mode, non-placeholder mutation token, required token scopes, migrated ledger schema, ledger hash-chain, operator-action journal, writable backup/artifact roots, deployment readiness, and a backup/restore drill. It intentionally keeps frontend readiness false unless `ui/strategist-web/package.json` exists in a future package.


## Single-tenant writable path envelope

The generated single-tenant Docker Compose and systemd templates run with a read-only root filesystem. The generated Compose template deliberately pins the Docker volume names to the `strategy-validator-ledger:/var/lib/strategy-validator` and `strategy-validator-backups:/var/backups/strategy-validator` volume bindings so the API container and one-shot helper containers operate on the same durable ledger and backup volumes. A valid `deployment.env` therefore keeps `STRATEGY_VALIDATOR_LEDGER_DB_PATH` and `STRATEGY_VALIDATOR_ARTIFACT_ROOT` under `/var/lib/strategy-validator`, and `STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR` under `/var/backups/strategy-validator`. The deployment env checker rejects paths outside those generated container writable roots so a config cannot pass validation and then fail at first boot.


Single-tenant generated-bundle checks now reject Compose lifecycle/runtime-contract drift, including missing `--env-file` usage in `commands/compose-up.sh` and `commands/compose-down.sh`, missing required env-file guards, missing absolute path canonicalization for custom env/Compose paths, missing `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` export, mismatched Compose runtime env files, missing or duplicated pinned volume names, and non-loopback host-port binds. The bundle checker also rejects helper env-path drift in `api-smoke`, preflight, ledger verify/backup/restore, and post-deploy evidence scripts so Docker `--env-file`, smoke, and evidence collection use the same canonical deployment env path instead of a caller-relative path. It rejects restore-helper drift that would allow host-local backup paths or pre-restore evidence outside `/var/backups/strategy-validator`, rejects post-deploy evidence mount drift that would make bundle, repo, or env inputs writable inside fallback containers, and rejects post-deploy path drift that leaves final evidence collection tied to caller-relative host paths.


Generated bundle verification also validates the generated Compose/systemd runtime contracts so widened host binds, wrong volume names, or unsafe systemd pre-start ordering are deployment-blocking even if a manifest was regenerated from drifted files.


The generated acceptance helper canonicalizes the deployment env file before selecting the local CLI or Docker fallback path, matching the rest of the single-tenant helper contract.
