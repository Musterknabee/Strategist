# Strategy Validator single-tenant deployment bundle

This bundle is generated for a **backend-only single-tenant** deployment.
It does not include or claim readiness for `ui/strategist-web`.

## Contents

- `manifest.json` — machine-readable bundle manifest.
- `deployment.env.redacted.json` — redacted env validation report; no raw tokens are copied.
- `repo-assets.manifest.json` — source repo asset digest manifest so target-host evidence does not need a source checkout.
- `.gitignore` — bundle-local guardrail preventing accidental commits of real `deployment.env`, evidence output, and local ledger backup artifacts.
- `docker-compose.single-tenant.yml` — Docker Compose template using `${STRATEGY_VALIDATOR_COMPOSE_ENV_FILE:-./deployment.env}` at deploy time with a read-only root filesystem, dropped Linux capabilities, no-new-privileges, and a tmpfs `/tmp`.
- `systemd/strategy-validator.service` — Docker-backed systemd template with the same container hardening flags and the same `STRATEGY_VALIDATOR_HOST_PORT` loopback bind policy as Compose, plus a pre-start deployment env validator.
- `commands/compose-up.sh` — Docker Compose start helper that validates `deployment.env` first and passes it with `--env-file` so host-port interpolation honors bundle-local settings.
- `commands/compose-down.sh` — Docker Compose stop helper using the same bundle-local Compose/env paths.
- `commands/preflight.sh` — containerized preflight command.
- `commands/api-smoke.sh` — self-locating HTTP smoke command for a running API; reads the bearer token and optional `STRATEGY_VALIDATOR_HOST_PORT`/`STRATEGY_VALIDATOR_BASE_URL` from `deployment.env` or the environment instead of requiring token argv.
- `commands/api-smoke.py` — bundled stdlib fallback smoke runner; no source checkout or host package install is required.
- `commands/verify-ledger.sh` — post-deploy combined ledger and operator-action journal integrity verification as one JSON report.
- `commands/backup-ledger.sh` — verified pre-change ledger backup helper.
- `commands/restore-ledger.sh` — guarded rollback restore helper requiring explicit confirmation, stopped-service acknowledgement, and a pre-restore copy of the displaced ledger.
- `commands/acceptance.sh` — self-locating go/no-go acceptance gate for env + bundle + repo-asset manifest, with Docker-image fallback when host CLIs are unavailable.
- `commands/post-deploy-evidence.sh` — self-locating post-deploy evidence pack collector for preflight, smoke, ledger verification, and backup reports, with Docker-image fallback for host CLI commands.

## Env validation status

`deployment.env` validation at bundle generation time: **PASS**.

If this is `FAIL`, fix the env file before deployment. The generated template files are still useful, but the manifest will mark the bundle as not deployment-ready.

## Minimal deployment flow

```bash
chmod 600 deployment.env
strategy-validator-deployment-env-check deployment.env --require-valid --json
bash commands/acceptance.sh
bash commands/preflight.sh
bash commands/compose-up.sh
bash commands/api-smoke.sh  # reads STRATEGY_VALIDATOR_API_TOKEN and optional host port/base URL from deployment.env or the environment
bash commands/verify-ledger.sh
bash commands/backup-ledger.sh
bash commands/post-deploy-evidence.sh
```

## Scope boundary

This bundle is not a multi-tenant SaaS package. It assumes one trusted operator deployment with durable local volumes for the SQLite ledger, backups, and artifacts. Keep the real `deployment.env` beside the bundle with private permissions such as `0600`; the env checker rejects secret-bearing POSIX env files that are group/world readable. For the generated Docker/systemd envelope, keep the ledger database and artifact root under `/var/lib/strategy-validator`, and the backup directory under `/var/backups/strategy-validator`; the env checker rejects paths outside those writable container volume roots. A target host needs either the packaged `strategy-validator-*` CLIs installed or Docker access to `STRATEGY_VALIDATOR_IMAGE` for generated helper fallbacks. Bundle command helpers self-locate `deployment.env` from the bundle root unless `STRATEGY_VALIDATOR_ENV_FILE` is explicitly supplied. Docker fallback helpers map host paths to fixed container paths (`/bundle`, `/repo`, `/env`, and `/evidence`) to avoid duplicate mount targets when bundle-local defaults are used. The API smoke helper derives its target from `STRATEGY_VALIDATOR_BASE_URL` when set, otherwise from `STRATEGY_VALIDATOR_HOST_PORT` in the environment or deployment env file, matching the generated Compose host-port binding. The generated Compose template binds the API to `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000`; because Docker Compose interpolation does not come from the service `env_file:` stanza, use `commands/compose-up.sh` so both interpolation and the API container runtime env use the same validated env file. If you run Compose manually with a non-default env path, set `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` to that same env file and pass `--env-file` explicitly. The generated systemd template sets `STRATEGY_VALIDATOR_HOST_PORT=8000` as a default and binds `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000`. Keep `STRATEGY_VALIDATOR_HOST_PORT` numeric and within `1..65535` so runtime binding and smoke target resolution stay aligned. The generated Compose file uses explicit Docker volume names (`strategy-validator-ledger` and `strategy-validator-backups`) so Compose-managed API containers and ad-hoc helper containers inspect, back up, verify, and restore the same durable ledger volumes.
