# Run the Strategy Validator API in Docker using ./deployment.env (gitignored).
# Prerequisites: Docker Desktop (or Linux engine) running; ./deployment.env must pass
#   python -m strategy_validator.cli.deployment_env_check deployment.env --require-valid
#
# Posture:
# - Named volumes persist ledger, artifacts, and backups across container removal.
# - Port bind is 127.0.0.1:8000 only (local loopback).
# - `docker restart` does not load new Python code; rebuild the image and recreate the container
#   to pick up app changes (e.g. new routes such as GET /).
# - Foreground `--rm` below is ideal for dev; for a long-running local service use a detached run, e.g.:
#     docker run -d --name strategist-local-api -p 127.0.0.1:8000:8000 `
#       -v strategist-local-lib:/var/lib/strategy-validator `
#       -v strategist-local-backups:/var/backups/strategy-validator `
#       --env-file deployment.env strategist-local
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Test-Path "deployment.env")) {
    Write-Error "Missing deployment.env. Copy deployment.env.sample, fill secrets, run deployment-env-check."
    exit 1
}
docker build -t strategist-local -f Dockerfile .
# Named volumes keep ledger, artifacts, and backups across container recreation (paths match Dockerfile).
docker volume create strategist-local-lib 2>$null | Out-Null
docker volume create strategist-local-backups 2>$null | Out-Null
# Bind host loopback only for local dev (avoid unintended LAN exposure).
docker run --rm -p 127.0.0.1:8000:8000 `
    -v strategist-local-lib:/var/lib/strategy-validator `
    -v strategist-local-backups:/var/backups/strategy-validator `
    --env-file deployment.env strategist-local
