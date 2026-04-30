# Single-tenant deployment readiness

This repo is ready to be hardened as a **single-tenant backend deployment** only. It does not include a frontend package, distributed workers, or a multi-tenant runtime.

## Required environment contract

Use `deployment.env.sample` as the operator template. A real deployment must provide:

| Variable | Required | Notes |
|---|---:|---|
| `STRATEGY_VALIDATOR_MODE=PRODUCTION` | yes | Enables fail-closed production behavior. |
| `STRATEGY_VALIDATOR_API_TOKEN` | yes | Must be a real secret, not `CHANGEME`, `replace-me`, `secret-token`, or another placeholder. |
| `STRATEGY_VALIDATOR_API_TOKEN_SCOPES` | yes | Must include `operator:command:write` and `operator:projection:read`. |
| `STRATEGY_VALIDATOR_LEDGER_DB_PATH` | yes | SQLite ledger database path under `/var/lib/strategy-validator` for the generated Docker/systemd envelope. |
| `STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR` | yes | Writable durable backup directory under `/var/backups/strategy-validator`. |
| `STRATEGY_VALIDATOR_ARTIFACT_ROOT` | yes | Writable operator artifact root under `/var/lib/strategy-validator`. |
| `STRATEGY_VALIDATOR_RESEARCH_API_TOKEN` | recommended | Separate token for research/advisory ingress. |
| `STRATEGY_VALIDATOR_HOST_PORT` | optional | Loopback host port used by generated Compose/systemd and smoke target derivation. Defaults to `8000`; must be numeric and within `1..65535`. |

## Validate a real deployment env file before use

Create a private `deployment.env` from `deployment.env.sample`, replace every `CHANGEME` value, lock down file permissions, then lint it without loading secrets into the shell:

```bash
chmod 600 deployment.env
strategy-validator-deployment-env-check deployment.env --require-valid --json
```

The env checker emits `single_tenant_deployment_env_check/v1` and blocks common deployment mistakes before container startup. For the generated Docker/systemd bundle, the writable root policy is intentionally strict: ledger and artifact paths must stay under `/var/lib/strategy-validator`, and backups must stay under `/var/backups/strategy-validator`. The optional `STRATEGY_VALIDATOR_HOST_PORT` is also validated here so Compose, systemd, and API smoke agree on the same loopback port before first boot.

- missing required production variables,
- non-production mode,
- placeholder or low-entropy-looking API tokens,
- missing `operator:command:write` / `operator:projection:read` scopes,
- relative ledger, backup, or artifact paths,
- ledger/artifact/backup paths outside the generated container writable volume roots,
- invalid `STRATEGY_VALIDATOR_HOST_PORT` values outside `1..65535` or non-numeric values,
- research token reuse warnings, configured placeholder research tokens as deployment-blocking errors,
- POSIX secret-bearing env files that are group/world readable.


## Bootstrap a fresh single-tenant volume

```bash
export STRATEGY_VALIDATOR_MODE=PRODUCTION
export STRATEGY_VALIDATOR_API_TOKEN='<real-random-token>'
export STRATEGY_VALIDATOR_API_TOKEN_SCOPES='operator:command:write,operator:projection:read'
export STRATEGY_VALIDATOR_LEDGER_DB_PATH=/var/lib/strategy-validator/ledger.sqlite3
export STRATEGY_VALIDATOR_LEDGER_BACKUP_DIR=/var/backups/strategy-validator
export STRATEGY_VALIDATOR_ARTIFACT_ROOT=/var/lib/strategy-validator/artifacts

strategy-validator-single-tenant-preflight \
  --prepare \
  --verify-backup-restore \
  --require-ready \
  --summary-markdown-output-path scratch/single-tenant-preflight.md \
  --json
```

`--prepare` creates the ledger parent, backup directory, artifact root, and applies SQLite migrations. Without `--prepare`, the command only verifies existing deployment state.

## Container smoke command

```bash
docker run --rm \
  --env-file deployment.env \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  strategy-validator-api:local \
  strategy-validator-single-tenant-preflight --prepare --verify-backup-restore --require-ready --json
```

After preflight passes, start the API normally:

```bash
docker run --rm \
  --env-file deployment.env \
  -p 127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000 \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  strategy-validator-api:local
```

## API HTTP smoke after startup

After the container is running, verify the booted HTTP surface from the host:

```bash
strategy-validator-single-tenant-api-smoke \
  --env-file deployment.env \
  --require-pass \
  --json
```

The packaged smoke command emits `single_tenant_api_http_smoke/v1` and verifies `/healthz`, `/readyz`, `/ui/facade`, unauthenticated mutation rejection, and authenticated UI command journaling. Prefer `--env-file deployment.env` or `STRATEGY_VALIDATOR_API_TOKEN` from the environment; `--token` is retained only for compatibility because command-line bearer tokens can appear in shell history and process listings. When `--base-url` is omitted, smoke derives the target from `STRATEGY_VALIDATOR_BASE_URL` if present, otherwise from `STRATEGY_VALIDATOR_HOST_PORT` in the environment or deployment env file, matching the generated Compose and systemd loopback port binding. Generated deployment bundles also carry `commands/api-smoke.py`, a standard-library fallback runner used by `commands/api-smoke.sh` when the package entrypoint is not installed on the target host. The source-tree `scripts/single_tenant_api_smoke.py` remains only a compatibility wrapper around the packaged console command.

## Readiness meaning

The preflight emits `single_tenant_deployment_preflight/v1` and requires all of the following before returning ready:

- production mode is active,
- mutation API token is configured and not placeholder-like,
- token scopes include command write and projection read,
- ledger schema/hash-chain verification passes,
- operator-action journal verification passes,
- backup directory and artifact root are writable,
- deployment readiness is `READY`,
- optional backup/restore drill passes when requested,
- frontend readiness is not claimed prematurely.

## Scope boundary

This is still backend-only. Do not expose it as a multi-tenant SaaS, do not claim `ui/strategist-web` readiness, and do not grant advisory/research routes capital authority.

## Generate a secret-safe deployment bundle

After validating a real private `deployment.env`, generate an operator handoff bundle:

```bash
strategy-validator-single-tenant-bundle \
  --env-file deployment.env \
  --output-dir scratch/single-tenant-deployment-bundle \
  --force \
  --require-ready \
  --json
```

The bundle emits `single_tenant_deployment_bundle/v1` and writes:

- `manifest.json` with generated file digests and backend-only deployment scope,
- `repo-assets.manifest.json` with source deployment-asset SHA-256/size evidence for target-host verification without a source checkout,
- `deployment.env.redacted.json` with token values redacted,
- `docker-compose.single-tenant.yml` with read-only root filesystem, dropped capabilities, no-new-privileges, and tmpfs `/tmp`,
- `systemd/strategy-validator.service` with matching Docker hardening flags and a hardened pre-start deployment env validator,
- `commands/compose-up.sh`,
- `commands/compose-down.sh`,
- `commands/preflight.sh`,
- `commands/api-smoke.sh`,
- `commands/api-smoke.py`,
- `commands/verify-ledger.sh`,
- `commands/backup-ledger.sh`,
- `commands/restore-ledger.sh`,
- `commands/acceptance.sh`,
- `commands/post-deploy-evidence.sh`,
- `README.md`.

The generator never copies raw API tokens into the bundle. It also keeps `frontend_readiness_claimed=false`; a future `ui/strategist-web` package must consume the backend `/ui/facade` contract separately. Bundle helper scripts are designed for target-host portability: `commands/compose-up.sh`, `commands/compose-down.sh`, `commands/preflight.sh`, `commands/verify-ledger.sh`, `commands/backup-ledger.sh`, `commands/restore-ledger.sh`, and `commands/acceptance.sh` self-locate `deployment.env` from the bundle root when `STRATEGY_VALIDATOR_ENV_FILE` is not supplied, then canonicalize custom env-file paths before invoking local CLIs or Docker fallbacks. Prefer `commands/compose-up.sh` over a raw `docker compose up` invocation, because Docker Compose interpolation for the `ports:` stanza does not come from service `env_file:`; the helper validates `deployment.env` first, canonicalizes custom env/Compose paths to absolute host paths, passes the validated env with `--env-file`, and exports `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` so Compose interpolation and the API container runtime `env_file` use the same validated file. Use `commands/compose-down.sh` for shutdown for the same reason: it now requires and canonicalizes the same deployment env file before calling Compose, so shutdown cannot silently drift to a caller-relative or missing env-file context. `commands/api-smoke.sh` can run the bundled `commands/api-smoke.py` and derives its target URL from `STRATEGY_VALIDATOR_BASE_URL` or `STRATEGY_VALIDATOR_HOST_PORT` so non-default Compose host ports do not create false smoke failures, while acceptance/evidence helpers can use Docker-image CLI fallbacks if the Python package is not installed on the host. Docker-backed acceptance/evidence fallbacks map host paths to fixed in-container mount points (`/bundle`, `/repo`, `/env`, and `/evidence`) so defaults do not create duplicate or conflicting Docker mounts when the bundle, env file, repo root, and evidence directory are colocated. Evidence fallback containers mount `/bundle`, `/repo`, and `/env` read-only and reserve read-write access for `/evidence` only, preventing a post-deploy collection run from mutating the handoff bundle or source inputs. `commands/post-deploy-evidence.sh` canonicalizes custom bundle, repo-root, env-file, and evidence-directory paths to absolute host paths before invoking local CLIs or Docker fallbacks, so relative operator overrides cannot make the final evidence manifest read from one location and write to another. Docker-backed helpers use a read-only root filesystem, dropped Linux capabilities, `no-new-privileges`, and a tmpfs `/tmp`. The generated systemd unit runs a hardened pre-start `strategy-validator-deployment-env-check` container against `/etc/strategy-validator/deployment.env` before stale-container cleanup. Only after that validation passes does it run ignored cleanup/stop lifecycle commands (`ExecStartPre=-...` and `ExecStop=-...`), so a bad env file does not remove an existing API container before failing closed; it still keeps first boot and already-stopped shutdown idempotent. The unit binds `127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000` so systemd deployments honor the same host-port env as Compose. The generated Compose file pins the durable volume names to the `strategy-validator-ledger:/var/lib/strategy-validator` and `strategy-validator-backups:/var/backups/strategy-validator` volume bindings; do not remove those `name:` fields unless you also update every generated helper script, because the scripts use those same named volumes for preflight, verification, backup, and restore. The restore helper is break-glass only: it requires explicit confirmation that the API is stopped, rejects backup paths outside the mounted `/var/backups/strategy-validator` volume, requires a `.sqlite3` backup artifact, and writes a pre-restore copy of the displaced ledger into `/var/backups/strategy-validator/pre-restore` before overwrite. Bundle verification checks the manifest digest inventory for generated files, validates the repo-asset manifest shape, rejects tampered or non-executable command helpers, enforces the expected Docker hardening flag counts, and validates the generated Compose lifecycle/runtime, helper env-path, and systemd runtime contracts so copy/paste drift such as duplicate tmpfs flags, missing no-new-privileges guards, caller-relative env-file use in Docker helpers, read-write evidence input mounts, caller-relative post-deploy evidence paths, widened host binds, wrong volume names, mismatched Compose env files, or unsafe systemd pre-start ordering is deployment-blocking.

To verify a generated bundle later:

```bash
strategy-validator-single-tenant-bundle \
  --output-dir scratch/single-tenant-deployment-bundle \
  --check \
  --require-ready \
  --json
```

## Final go/no-go acceptance report

Before deploying to a single-tenant host, generate and verify the bundle, then emit a final backend-only acceptance report:

```bash
strategy-validator-single-tenant-acceptance \
  --env-file deployment.env \
  --bundle-dir scratch/single-tenant-deployment-bundle \
  --summary-markdown-output-path scratch/single-tenant-acceptance.md \
  --require-ready \
  --json
```

The command emits `single_tenant_deployment_acceptance/v1` and verifies:

- the private deployment env passes `single_tenant_deployment_env_check/v1`,
- required backend deployment repo assets exist, or are covered by `repo-assets.manifest.json` when no source checkout is present,
- source deployment assets match the bundle-recorded repo-asset SHA-256/size evidence when a source checkout is present,
- the generated deployment bundle verifies, including generated-file SHA-256/size evidence, repo-asset manifest integrity, and command executable bits,
- bundle helper scripts exist for preflight, API smoke, ledger verification, backup, guarded restore, and acceptance,
- no frontend readiness is claimed.

The generated bundle now also includes rollback-oriented helpers:

- `commands/verify-ledger.sh` emits one `ledger_ops_integrity_verify/v1` JSON report covering ledger schema/hash-chain and operator-action journal integrity inside the container image,
- `commands/backup-ledger.sh` creates a verified SQLite backup before risky changes,
- `commands/restore-ledger.sh` performs a guarded restore only when `STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH` is a container-visible `.sqlite3` path under `/var/backups/strategy-validator`, `STRATEGY_VALIDATOR_CONFIRM_API_STOPPED=YES`, and `STRATEGY_VALIDATOR_CONFIRM_RESTORE=YES` are set, and it emits `ledger_ops_pre_restore_backup/v1` evidence for the displaced ledger,
- `commands/acceptance.sh` runs the acceptance gate against the env + bundle, self-locates the bundle root when run from any working directory, canonicalizes the deployment env file before local or Docker execution, and falls back to `docker run` with `STRATEGY_VALIDATOR_IMAGE` when the host CLI is unavailable.

For rollback, stop the API first, select the verified backup path, and run:

```bash
# This path is inside the helper container and must live under the mounted backup volume.
export STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH=/var/backups/strategy-validator/<backup>.sqlite3
export STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR=/var/backups/strategy-validator/pre-restore
export STRATEGY_VALIDATOR_CONFIRM_API_STOPPED=YES
export STRATEGY_VALIDATOR_CONFIRM_RESTORE=YES
bash commands/restore-ledger.sh
bash commands/verify-ledger.sh
```

This is still a backend-only single-tenant process. It does not certify `ui/strategist-web`, multi-tenant isolation, or SaaS operations.

## Deployment evidence pack

After the backend is deployed and the API smoke has passed, preserve a secret-safe evidence pack for the single-tenant deployment:

```bash
mkdir -p scratch/single-tenant-deployment-evidence
strategy-validator-deployment-env-check deployment.env --require-valid --json \
  > scratch/single-tenant-deployment-evidence/deployment-env-check.json
strategy-validator-single-tenant-bundle --output-dir scratch/single-tenant-deployment-bundle --check --require-ready --json \
  > scratch/single-tenant-deployment-evidence/deployment-bundle.json
strategy-validator-single-tenant-acceptance \
  --env-file deployment.env \
  --bundle-dir scratch/single-tenant-deployment-bundle \
  --summary-markdown-output-path scratch/single-tenant-deployment-evidence/deployment-acceptance.md \
  --require-ready \
  --json > scratch/single-tenant-deployment-evidence/deployment-acceptance.json
```

The generated deployment bundle also contains a self-locating evidence collector:

```bash
bash commands/post-deploy-evidence.sh
```

By default it reads `deployment.env` from the bundle root, writes `evidence/` under the bundle root, and uses the bundle `repo-assets.manifest.json` instead of requiring a full source checkout on the target host. If you override `STRATEGY_VALIDATOR_BUNDLE_DIR`, `STRATEGY_VALIDATOR_REPO_ROOT`, `STRATEGY_VALIDATOR_ENV_FILE`, or `STRATEGY_VALIDATOR_EVIDENCE_DIR`, the helper resolves them to absolute host paths before collecting evidence. For host-side checks, it uses installed `strategy-validator-*` CLIs when present and otherwise falls back to running those CLIs inside `STRATEGY_VALIDATOR_IMAGE` with the bundle/evidence paths mounted.

That helper collects preflight, API smoke, a combined `ledger_ops_integrity_verify/v1` ledger verification report, and backup reports, then runs:

```bash
strategy-validator-single-tenant-evidence \
  --evidence-dir scratch/single-tenant-deployment-evidence \
  --final \
  --require-pass \
  --manifest-output-path scratch/single-tenant-deployment-evidence/deployment-evidence.json \
  --summary-markdown-output-path scratch/single-tenant-deployment-evidence/deployment-evidence.md \
  --json
```

The evidence command emits `single_tenant_deployment_evidence/v1`. It records schema versions, file sizes, and SHA-256 digests of deployment reports. The ledger backup report also carries the backup artifact SHA-256. The evidence collector does not copy raw token values and it continues to report `frontend_readiness_claimed=false` for backend-only deployment.


Single-tenant generated-bundle checks now reject Compose runtime-contract drift, including missing or duplicated pinned volume names and non-loopback host-port binds.
