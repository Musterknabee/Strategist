"""Generate a backend-only single-tenant deployment bundle.

The bundle is intentionally operator-facing and secret-safe: it validates the
operator env file, emits a redacted summary, and writes reproducible deployment
helpers without copying raw secrets into the generated artifact directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from strategy_validator.cli.deployment_env_check import (
    EnvCheckReport,
    build_single_tenant_deployment_env_check,
    parse_env_file,
)

_SCHEMA_VERSION = "single_tenant_deployment_bundle/v1"
_FRONTEND_PACKAGE = "ui/strategist-web"
_DEFAULT_OUTPUT_DIR = "scratch/single-tenant-deployment-bundle"
_REPO_ASSET_SCHEMA_VERSION = "single_tenant_repo_assets_manifest/v1"
_REQUIRED_REPO_ASSETS = (
    "Dockerfile",
    "deployment.env.sample",
    "docs/deployment/SINGLE_TENANT_DEPLOYMENT_READINESS.md",
    "scripts/single_tenant_api_smoke.py",
    "strategy_validator/cli/single_tenant_preflight.py",
    "strategy_validator/cli/deployment_env_check.py",
    "strategy_validator/cli/single_tenant_deployment_bundle.py",
    "strategy_validator/cli/single_tenant_deployment_acceptance.py",
    "strategy_validator/cli/single_tenant_deployment_evidence.py",
)

_SECRET_KEY_MARKERS = ("TOKEN", "SECRET", "PASSWORD", "KEY")
_REQUIRED_GENERATED_FILES = (
    "manifest.json",
    "deployment.env.redacted.json",
    "repo-assets.manifest.json",
    ".gitignore",
    "docker-compose.single-tenant.yml",
    "systemd/strategy-validator.service",
    "commands/compose-up.sh",
    "commands/compose-down.sh",
    "commands/preflight.sh",
    "commands/api-smoke.sh",
    "commands/api-smoke.py",
    "commands/verify-ledger.sh",
    "commands/backup-ledger.sh",
    "commands/restore-ledger.sh",
    "commands/acceptance.sh",
    "commands/post-deploy-evidence.sh",
    "README.md",
)


@dataclass(frozen=True)
class GeneratedFile:
    path: str
    sha256: str
    size_bytes: int


@dataclass(frozen=True)
class DeploymentBundleReport:
    schema_version: str
    ok: bool
    output_dir: str
    env_file: str
    generated_at_utc: str
    deployment_model: str
    frontend_expected_package: str
    frontend_package_present: bool
    frontend_readiness_claimed: bool
    env_check_ok: bool
    generated_files: tuple[GeneratedFile, ...]
    errors: tuple[str, ...]

    def to_payload(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "ok": self.ok,
            "output_dir": self.output_dir,
            "env_file": self.env_file,
            "generated_at_utc": self.generated_at_utc,
            "deployment_model": self.deployment_model,
            "frontend_expected_package": self.frontend_expected_package,
            "frontend_package_present": self.frontend_package_present,
            "frontend_readiness_claimed": self.frontend_readiness_claimed,
            "env_check_ok": self.env_check_ok,
            "generated_files": [asdict(item) for item in self.generated_files],
            "errors": list(self.errors),
        }


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(text, encoding="utf-8")
    if executable:
        tmp.chmod(0o755)
    tmp.replace(path)


def _is_secret_key(key: str) -> bool:
    upper = key.upper()
    return any(marker in upper for marker in _SECRET_KEY_MARKERS)


def _redact_value(key: str, value: str) -> str:
    if not _is_secret_key(key):
        return value
    if not value:
        return ""
    return f"<redacted:{len(value)} chars>"


def _redacted_env_payload(env_file: Path, env_check: EnvCheckReport) -> dict[str, object]:
    values, parse_issues = parse_env_file(env_file)
    return {
        "schema_version": "single_tenant_deployment_env_redacted/v1",
        "env_file": str(env_file),
        "env_check": env_check.to_payload(),
        "values": {key: _redact_value(key, values[key]) for key in sorted(values)},
        "parse_issue_count": len(parse_issues),
    }


def _repo_asset_manifest(repo_root: Path, *, generated_at_utc: str) -> dict[str, object]:
    assets: list[dict[str, object]] = []
    for relative in _REQUIRED_REPO_ASSETS:
        path = repo_root / relative
        exists = path.is_file()
        assets.append(
            {
                "path": relative,
                "exists": exists,
                "sha256": _sha256_file(path) if exists else None,
                "size_bytes": path.stat().st_size if exists else None,
            }
        )
    missing = [str(item["path"]) for item in assets if not item["exists"]]
    return {
        "schema_version": _REPO_ASSET_SCHEMA_VERSION,
        "generated_at_utc": generated_at_utc,
        "repo_root": str(repo_root),
        "asset_count": len(assets),
        "missing_asset_count": len(missing),
        "missing_assets": missing,
        "assets": assets,
    }


def _bundle_gitignore() -> str:
    return """# Generated single-tenant handoff bundle local guardrails.
# Keep real secrets and deployment evidence out of source control.
deployment.env
.env
*.env
evidence/
*.sqlite3
*.sqlite3-*
*.db
*.db-*
backups/
pre-restore/
"""


def _compose_template() -> str:
    return """# Backend-only single-tenant deployment template.
# Generated by strategy-validator-single-tenant-bundle.
# Do not commit real deployment.env files.
services:
  strategy-validator-api:
    image: ${STRATEGY_VALIDATOR_IMAGE:-strategy-validator-api:local}
    container_name: strategy-validator-api
    restart: unless-stopped
    env_file:
      - ${STRATEGY_VALIDATOR_COMPOSE_ENV_FILE:-./deployment.env}
    ports:
      - "127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000"
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
    tmpfs:
      - /tmp:rw,nosuid,nodev,noexec,size=64m
    volumes:
      - strategy-validator-ledger:/var/lib/strategy-validator
      - strategy-validator-backups:/var/backups/strategy-validator
    healthcheck:
      test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=3).read()"]
      interval: 30s
      timeout: 5s
      retries: 5
      start_period: 20s

volumes:
  strategy-validator-ledger:
    name: strategy-validator-ledger
  strategy-validator-backups:
    name: strategy-validator-backups
"""


def _systemd_template() -> str:
    return r"""# Backend-only single-tenant Docker service template.
# Copy to /etc/systemd/system/strategy-validator.service and adjust paths/image.
[Unit]
Description=Strategy Validator single-tenant backend API
After=network-online.target docker.service
Wants=network-online.target
Requires=docker.service

[Service]
Type=simple
Environment=STRATEGY_VALIDATOR_IMAGE=strategy-validator-api:local
Environment=STRATEGY_VALIDATOR_HOST_PORT=8000
EnvironmentFile=/etc/strategy-validator/deployment.env
ExecStartPre=/usr/bin/docker run --rm --user 0:0 \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -v /etc/strategy-validator:/deployment-env:ro \
  ${STRATEGY_VALIDATOR_IMAGE} \
  strategy-validator-deployment-env-check /deployment-env/deployment.env --require-valid --json
ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api
ExecStart=/usr/bin/docker run --rm --name strategy-validator-api \
  --env-file /etc/strategy-validator/deployment.env \
  -p 127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000 \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  ${STRATEGY_VALIDATOR_IMAGE}
ExecStop=-/usr/bin/docker stop strategy-validator-api
Restart=on-failure
RestartSec=5s
TimeoutStartSec=120

[Install]
WantedBy=multi-user.target
"""


def _compose_up_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_COMPOSE_FILE:=${BUNDLE_DIR}/docker-compose.single-tenant.yml}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

if [[ ! -f "${STRATEGY_VALIDATOR_COMPOSE_FILE}" ]]; then
  echo "Compose file not found: ${STRATEGY_VALIDATOR_COMPOSE_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"

HOST_COMPOSE_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_COMPOSE_FILE}")" && pwd)"
HOST_COMPOSE_BASENAME="$(basename "${STRATEGY_VALIDATOR_COMPOSE_FILE}")"
STRATEGY_VALIDATOR_COMPOSE_FILE="${HOST_COMPOSE_DIR}/${HOST_COMPOSE_BASENAME}"

# Validate the exact env file before Compose interpolation. Compose service
# env_file entries do not supply variables for ports interpolation; the explicit
# --env-file below is therefore part of the generated deployment contract.
docker run --rm --user 0:0 \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  -v "${HOST_ENV_DIR}:/deployment-env:ro" \
  "${STRATEGY_VALIDATOR_IMAGE}" \
  strategy-validator-deployment-env-check "/deployment-env/${HOST_ENV_BASENAME}" --require-valid --json >/dev/null

compose_cmd=()
if docker compose version >/dev/null 2>&1; then
  compose_cmd=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose_cmd=(docker-compose)
else
  echo "No Docker Compose runner found. Install Docker Compose v2 or docker-compose." >&2
  exit 127
fi

export STRATEGY_VALIDATOR_COMPOSE_ENV_FILE="${STRATEGY_VALIDATOR_ENV_FILE}"

exec "${compose_cmd[@]}" \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -f "${STRATEGY_VALIDATOR_COMPOSE_FILE}" \
  up -d
"""


def _compose_down_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_COMPOSE_FILE:=${BUNDLE_DIR}/docker-compose.single-tenant.yml}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

if [[ ! -f "${STRATEGY_VALIDATOR_COMPOSE_FILE}" ]]; then
  echo "Compose file not found: ${STRATEGY_VALIDATOR_COMPOSE_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

HOST_COMPOSE_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_COMPOSE_FILE}")" && pwd)"
HOST_COMPOSE_BASENAME="$(basename "${STRATEGY_VALIDATOR_COMPOSE_FILE}")"
STRATEGY_VALIDATOR_COMPOSE_FILE="${HOST_COMPOSE_DIR}/${HOST_COMPOSE_BASENAME}"

compose_cmd=()
if docker compose version >/dev/null 2>&1; then
  compose_cmd=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
  compose_cmd=(docker-compose)
else
  echo "No Docker Compose runner found. Install Docker Compose v2 or docker-compose." >&2
  exit 127
fi

export STRATEGY_VALIDATOR_COMPOSE_ENV_FILE="${STRATEGY_VALIDATOR_ENV_FILE}"

exec "${compose_cmd[@]}" \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -f "${STRATEGY_VALIDATOR_COMPOSE_FILE}" \
  down
"""


def _preflight_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  "${STRATEGY_VALIDATOR_IMAGE}" \
  strategy-validator-single-tenant-preflight \
    --prepare \
    --verify-backup-restore \
    --require-ready \
    --repo-root /app \
    --json
"""


def _api_smoke_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_OPERATOR_ID:=single-tenant-smoke}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_API_TOKEN_ENV_VAR:=STRATEGY_VALIDATOR_API_TOKEN}"

if [[ -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
  HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
  STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
  export STRATEGY_VALIDATOR_ENV_FILE
fi

args=(
  --token-env-var "${STRATEGY_VALIDATOR_API_TOKEN_ENV_VAR}"
  --operator-id "${STRATEGY_VALIDATOR_OPERATOR_ID}"
  --require-pass
  --json
)

if [[ -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  args+=(--env-file "${STRATEGY_VALIDATOR_ENV_FILE}")
fi

if [[ -n "${STRATEGY_VALIDATOR_BASE_URL:-}" ]]; then
  args+=(--base-url "${STRATEGY_VALIDATOR_BASE_URL}")
fi

if command -v strategy-validator-single-tenant-api-smoke >/dev/null 2>&1; then
  exec strategy-validator-single-tenant-api-smoke "${args[@]}"
fi

if command -v python3 >/dev/null 2>&1 && [[ -f "${SCRIPT_DIR}/api-smoke.py" ]]; then
  exec python3 "${SCRIPT_DIR}/api-smoke.py" "${args[@]}"
fi

if command -v python >/dev/null 2>&1 && [[ -f "${SCRIPT_DIR}/api-smoke.py" ]]; then
  exec python "${SCRIPT_DIR}/api-smoke.py" "${args[@]}"
fi

echo "No smoke runner available. Install strategy-validator, provide python3, or keep commands/api-smoke.py in the bundle." >&2
exit 127
"""


def _api_smoke_python_script() -> str:
    return (Path(__file__).with_name("single_tenant_api_smoke.py").read_text(encoding="utf-8"))


def _verify_ledger_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  "${STRATEGY_VALIDATOR_IMAGE}" \
  strategy-validator-ledger-ops verify-integrity --json
"""


def _backup_ledger_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  "${STRATEGY_VALIDATOR_IMAGE}" \
  strategy-validator-ledger-ops backup --json
"""


def _restore_ledger_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH:?Set STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH to the container-visible backup .sqlite3 path to restore}"
: "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR:=/var/backups/strategy-validator/pre-restore}"
: "${STRATEGY_VALIDATOR_CONFIRM_API_STOPPED:?Set STRATEGY_VALIDATOR_CONFIRM_API_STOPPED=YES after stopping the API container/service}"
: "${STRATEGY_VALIDATOR_CONFIRM_RESTORE:?Set STRATEGY_VALIDATOR_CONFIRM_RESTORE=YES after confirming rollback intent}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

BACKUP_ROOT="/var/backups/strategy-validator"
if [[ "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}" != "${BACKUP_ROOT}/"* || "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}" != *.sqlite3 ]]; then
  echo "Refusing restore: STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH must be a container-visible .sqlite3 path under ${BACKUP_ROOT}" >&2
  exit 2
fi

if [[ "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}" != "${BACKUP_ROOT}" && "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}" != "${BACKUP_ROOT}/"* ]]; then
  echo "Refusing restore: STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR must be under ${BACKUP_ROOT}" >&2
  exit 2
fi

if [[ "${STRATEGY_VALIDATOR_CONFIRM_API_STOPPED}" != "YES" ]]; then
  echo "Refusing restore: STRATEGY_VALIDATOR_CONFIRM_API_STOPPED must equal YES" >&2
  exit 2
fi

if [[ "${STRATEGY_VALIDATOR_CONFIRM_RESTORE}" != "YES" ]]; then
  echo "Refusing restore: STRATEGY_VALIDATOR_CONFIRM_RESTORE must equal YES" >&2
  exit 2
fi

docker run --rm \
  --read-only \
  --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
  --cap-drop ALL \
  --security-opt no-new-privileges:true \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  -v strategy-validator-ledger:/var/lib/strategy-validator \
  -v strategy-validator-backups:/var/backups/strategy-validator \
  "${STRATEGY_VALIDATOR_IMAGE}" \
  strategy-validator-ledger-ops restore \
    --backup-path "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}" \
    --pre-restore-backup-dir "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}" \
    --allow-overwrite \
    --json
"""


def _acceptance_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_REPO_ROOT:=${BUNDLE_DIR}}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_BUNDLE_DIR:=${BUNDLE_DIR}}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

HOST_BUNDLE_DIR="$(cd "${STRATEGY_VALIDATOR_BUNDLE_DIR}" && pwd)"
HOST_REPO_ROOT="$(cd "${STRATEGY_VALIDATOR_REPO_ROOT}" && pwd)"
HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE

host_args=(
  --repo-root "${HOST_REPO_ROOT}"
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}"
  --bundle-dir "${HOST_BUNDLE_DIR}"
  --require-ready
  --json
)

container_args=(
  --repo-root /repo
  --env-file "/env/${HOST_ENV_BASENAME}"
  --bundle-dir /bundle
  --require-ready
  --json
)

if command -v strategy-validator-single-tenant-acceptance >/dev/null 2>&1; then
  exec strategy-validator-single-tenant-acceptance "${host_args[@]}"
fi

if command -v docker >/dev/null 2>&1; then
  exec docker run --rm \
    --read-only \
    --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
    --cap-drop ALL \
    --security-opt no-new-privileges:true \
    -v "${HOST_BUNDLE_DIR}:/bundle:ro" \
    -v "${HOST_REPO_ROOT}:/repo:ro" \
    -v "${HOST_ENV_DIR}:/env:ro" \
    -w /bundle \
    "${STRATEGY_VALIDATOR_IMAGE}" \
    strategy-validator-single-tenant-acceptance "${container_args[@]}"
fi

echo "No acceptance runner available. Install strategy-validator or provide Docker with STRATEGY_VALIDATOR_IMAGE." >&2
exit 127
"""



def _post_deploy_evidence_script() -> str:
    return r"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUNDLE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"

: "${STRATEGY_VALIDATOR_IMAGE:=strategy-validator-api:local}"
: "${STRATEGY_VALIDATOR_REPO_ROOT:=${BUNDLE_DIR}}"
: "${STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env}"
: "${STRATEGY_VALIDATOR_BUNDLE_DIR:=${BUNDLE_DIR}}"
: "${STRATEGY_VALIDATOR_EVIDENCE_DIR:=${BUNDLE_DIR}/evidence}"
: "${STRATEGY_VALIDATOR_OPERATOR_ID:=single-tenant-evidence}"

if [[ ! -f "${STRATEGY_VALIDATOR_ENV_FILE}" ]]; then
  echo "deployment env file not found: ${STRATEGY_VALIDATOR_ENV_FILE}" >&2
  exit 2
fi

mkdir -p "${STRATEGY_VALIDATOR_EVIDENCE_DIR}"

HOST_BUNDLE_DIR="$(cd "${STRATEGY_VALIDATOR_BUNDLE_DIR}" && pwd)"
STRATEGY_VALIDATOR_BUNDLE_DIR="${HOST_BUNDLE_DIR}"
export STRATEGY_VALIDATOR_BUNDLE_DIR
HOST_REPO_ROOT="$(cd "${STRATEGY_VALIDATOR_REPO_ROOT}" && pwd)"
STRATEGY_VALIDATOR_REPO_ROOT="${HOST_REPO_ROOT}"
export STRATEGY_VALIDATOR_REPO_ROOT
HOST_ENV_DIR="$(cd "$(dirname "${STRATEGY_VALIDATOR_ENV_FILE}")" && pwd)"
HOST_ENV_BASENAME="$(basename "${STRATEGY_VALIDATOR_ENV_FILE}")"
STRATEGY_VALIDATOR_ENV_FILE="${HOST_ENV_DIR}/${HOST_ENV_BASENAME}"
export STRATEGY_VALIDATOR_ENV_FILE
HOST_EVIDENCE_DIR="$(cd "${STRATEGY_VALIDATOR_EVIDENCE_DIR}" && pwd)"
STRATEGY_VALIDATOR_EVIDENCE_DIR="${HOST_EVIDENCE_DIR}"
export STRATEGY_VALIDATOR_EVIDENCE_DIR

CONTAINER_BUNDLE_DIR=/bundle
CONTAINER_REPO_ROOT=/repo
CONTAINER_ENV_FILE="/env/${HOST_ENV_BASENAME}"
CONTAINER_EVIDENCE_DIR=/evidence

run_cli() {
  local command_name="$1"
  shift
  local host_args=()
  local container_args=()
  local parsing_container=0
  for arg in "$@"; do
    if [[ "${arg}" == "__CONTAINER_ARGS__" ]]; then
      parsing_container=1
      continue
    fi
    if [[ "${parsing_container}" -eq 0 ]]; then
      host_args+=("${arg}")
    else
      container_args+=("${arg}")
    fi
  done
  if [[ "${#container_args[@]}" -eq 0 ]]; then
    container_args=("${host_args[@]}")
  fi

  if command -v "${command_name}" >/dev/null 2>&1; then
    "${command_name}" "${host_args[@]}"
    return
  fi
  if command -v docker >/dev/null 2>&1; then
    docker run --rm \
      --read-only \
      --tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m \
      --cap-drop ALL \
      --security-opt no-new-privileges:true \
      -v "${HOST_BUNDLE_DIR}:${CONTAINER_BUNDLE_DIR}:ro" \
      -v "${HOST_REPO_ROOT}:${CONTAINER_REPO_ROOT}:ro" \
      -v "${HOST_ENV_DIR}:/env:ro" \
      -v "${HOST_EVIDENCE_DIR}:${CONTAINER_EVIDENCE_DIR}:rw" \
      -w "${CONTAINER_BUNDLE_DIR}" \
      "${STRATEGY_VALIDATOR_IMAGE}" \
      "${command_name}" "${container_args[@]}"
    return
  fi
  echo "No runner available for ${command_name}. Install strategy-validator or provide Docker with STRATEGY_VALIDATOR_IMAGE." >&2
  return 127
}

run_cli strategy-validator-deployment-env-check \
  "${STRATEGY_VALIDATOR_ENV_FILE}" --require-valid --json \
  __CONTAINER_ARGS__ "${CONTAINER_ENV_FILE}" --require-valid --json \
  > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-env-check.json"

run_cli strategy-validator-single-tenant-bundle \
  --output-dir "${STRATEGY_VALIDATOR_BUNDLE_DIR}" --check --require-ready --json \
  __CONTAINER_ARGS__ --output-dir "${CONTAINER_BUNDLE_DIR}" --check --require-ready --json \
  > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-bundle.json"

run_cli strategy-validator-single-tenant-acceptance \
  --repo-root "${STRATEGY_VALIDATOR_REPO_ROOT}" \
  --env-file "${STRATEGY_VALIDATOR_ENV_FILE}" \
  --bundle-dir "${STRATEGY_VALIDATOR_BUNDLE_DIR}" \
  --require-ready \
  --json \
  __CONTAINER_ARGS__ \
  --repo-root "${CONTAINER_REPO_ROOT}" \
  --env-file "${CONTAINER_ENV_FILE}" \
  --bundle-dir "${CONTAINER_BUNDLE_DIR}" \
  --require-ready \
  --json \
  > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-acceptance.json"

bash "${BUNDLE_DIR}/commands/preflight.sh" > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/preflight.json"

bash "${BUNDLE_DIR}/commands/api-smoke.sh" > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/api-smoke.json"

bash "${BUNDLE_DIR}/commands/verify-ledger.sh" > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/ledger-verify.json"

bash "${BUNDLE_DIR}/commands/backup-ledger.sh" > "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/ledger-backup.json"

run_cli strategy-validator-single-tenant-evidence \
  --evidence-dir "${STRATEGY_VALIDATOR_EVIDENCE_DIR}" \
  --repo-root "${STRATEGY_VALIDATOR_REPO_ROOT}" \
  --final \
  --require-pass \
  --manifest-output-path "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-evidence.json" \
  --summary-markdown-output-path "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-evidence.md" \
  --json \
  __CONTAINER_ARGS__ \
  --evidence-dir "${CONTAINER_EVIDENCE_DIR}" \
  --repo-root "${CONTAINER_REPO_ROOT}" \
  --final \
  --require-pass \
  --manifest-output-path "${CONTAINER_EVIDENCE_DIR}/deployment-evidence.json" \
  --summary-markdown-output-path "${CONTAINER_EVIDENCE_DIR}/deployment-evidence.md" \
  --json
"""

def _readme(env_check: EnvCheckReport) -> str:
    status = "PASS" if env_check.ok else "FAIL"
    return f"""# Strategy Validator single-tenant deployment bundle

This bundle is generated for a **backend-only single-tenant** deployment.
It does not include or claim readiness for `{_FRONTEND_PACKAGE}`.

## Contents

- `manifest.json` — machine-readable bundle manifest.
- `deployment.env.redacted.json` — redacted env validation report; no raw tokens are copied.
- `repo-assets.manifest.json` — source repo asset digest manifest so target-host evidence does not need a source checkout.
- `.gitignore` — bundle-local guardrail preventing accidental commits of real `deployment.env`, evidence output, and local ledger backup artifacts.
- `docker-compose.single-tenant.yml` — Docker Compose template using `${{STRATEGY_VALIDATOR_COMPOSE_ENV_FILE:-./deployment.env}}` at deploy time with a read-only root filesystem, dropped Linux capabilities, no-new-privileges, and a tmpfs `/tmp`.
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

`deployment.env` validation at bundle generation time: **{status}**.

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

This bundle is not a multi-tenant SaaS package. It assumes one trusted operator deployment with durable local volumes for the SQLite ledger, backups, and artifacts. Keep the real `deployment.env` beside the bundle with private permissions such as `0600`; the env checker rejects secret-bearing POSIX env files that are group/world readable. For the generated Docker/systemd envelope, keep the ledger database and artifact root under `/var/lib/strategy-validator`, and the backup directory under `/var/backups/strategy-validator`; the env checker rejects paths outside those writable container volume roots. A target host needs either the packaged `strategy-validator-*` CLIs installed or Docker access to `STRATEGY_VALIDATOR_IMAGE` for generated helper fallbacks. Bundle command helpers self-locate `deployment.env` from the bundle root unless `STRATEGY_VALIDATOR_ENV_FILE` is explicitly supplied. Docker fallback helpers map host paths to fixed container paths (`/bundle`, `/repo`, `/env`, and `/evidence`) to avoid duplicate mount targets when bundle-local defaults are used. The API smoke helper derives its target from `STRATEGY_VALIDATOR_BASE_URL` when set, otherwise from `STRATEGY_VALIDATOR_HOST_PORT` in the environment or deployment env file, matching the generated Compose host-port binding. The generated Compose template binds the API to `127.0.0.1:${{STRATEGY_VALIDATOR_HOST_PORT:-8000}}:8000`; because Docker Compose interpolation does not come from the service `env_file:` stanza, use `commands/compose-up.sh` so both interpolation and the API container runtime env use the same validated env file. If you run Compose manually with a non-default env path, set `STRATEGY_VALIDATOR_COMPOSE_ENV_FILE` to that same env file and pass `--env-file` explicitly. The generated systemd template sets `STRATEGY_VALIDATOR_HOST_PORT=8000` as a default and binds `127.0.0.1:${{STRATEGY_VALIDATOR_HOST_PORT}}:8000`. Keep `STRATEGY_VALIDATOR_HOST_PORT` numeric and within `1..65535` so runtime binding and smoke target resolution stay aligned. The generated Compose file uses explicit Docker volume names (`strategy-validator-ledger` and `strategy-validator-backups`) so Compose-managed API containers and ad-hoc helper containers inspect, back up, verify, and restore the same durable ledger volumes.
"""




def _is_safe_bundle_relative_path(value: object) -> bool:
    if not isinstance(value, str) or not value:
        return False
    candidate = Path(value)
    if candidate.is_absolute():
        return False
    return ".." not in candidate.parts


def _manifest_generated_file_entries(manifest: dict[str, object]) -> dict[str, dict[str, object]]:
    raw_entries = manifest.get("generated_files", [])
    if not isinstance(raw_entries, list):
        return {}
    entries: dict[str, dict[str, object]] = {}
    for item in raw_entries:
        if not isinstance(item, dict):
            continue
        path = item.get("path")
        if _is_safe_bundle_relative_path(path):
            entries[str(path)] = item
    return entries


def _verify_manifest_generated_file_digests(out: Path, manifest: dict[str, object]) -> list[str]:
    """Verify that manifest-listed bundle assets still match size/digest evidence."""

    errors: list[str] = []
    raw_entries = manifest.get("generated_files", [])
    if not isinstance(raw_entries, list):
        return ["manifest generated_files is not a list"]

    entries = _manifest_generated_file_entries(manifest)
    for item in raw_entries:
        if not isinstance(item, dict):
            errors.append("manifest generated_files contains a non-object entry")
            continue
        relative = item.get("path")
        if not _is_safe_bundle_relative_path(relative):
            errors.append(f"manifest generated_files contains unsafe path: {relative!r}")
            continue
        relative_str = str(relative)
        if relative_str == "manifest.json":
            # The manifest cannot self-hash stably.  It is validated by schema
            # checks above and explicitly excluded from generated_files on write.
            errors.append("manifest generated_files must not include manifest.json self-reference")
            continue
        path = out / relative_str
        if not path.is_file():
            errors.append(f"manifest-listed generated file missing: {relative_str}")
            continue

        expected_size = item.get("size_bytes")
        expected_sha256 = item.get("sha256")
        actual_size = path.stat().st_size
        actual_sha256 = _sha256_file(path)
        if expected_size != actual_size:
            errors.append(
                f"manifest-listed generated file size mismatch: {relative_str} "
                f"expected={expected_size!r} actual={actual_size}"
            )
        if expected_sha256 != actual_sha256:
            errors.append(
                f"manifest-listed generated file sha256 mismatch: {relative_str} "
                f"expected={expected_sha256!r} actual={actual_sha256}"
            )

    for relative in _REQUIRED_GENERATED_FILES:
        if relative == "manifest.json":
            continue
        if relative not in entries:
            errors.append(f"required generated file missing from manifest digest inventory: {relative}")

    return errors




def _is_valid_sha256(value: object) -> bool:
    return isinstance(value, str) and bool(re.fullmatch(r"[0-9a-f]{64}", value))


def _verify_repo_asset_manifest_payload(repo_assets: object) -> list[str]:
    """Validate the portable source-asset manifest carried in the bundle."""

    errors: list[str] = []
    if not isinstance(repo_assets, dict):
        return ["repo-assets.manifest.json is not a JSON object"]
    if repo_assets.get("schema_version") != _REPO_ASSET_SCHEMA_VERSION:
        errors.append("repo-assets.manifest.json schema_version is not single_tenant_repo_assets_manifest/v1")

    missing_count = repo_assets.get("missing_asset_count")
    if missing_count not in {0, 0.0}:
        errors.append("repo-assets.manifest.json records missing required repo assets")

    assets = repo_assets.get("assets")
    if not isinstance(assets, list):
        errors.append("repo-assets.manifest.json assets is not a list")
        return errors

    by_path: dict[str, dict[str, object]] = {}
    for item in assets:
        if not isinstance(item, dict):
            errors.append("repo-assets.manifest.json assets contains a non-object entry")
            continue
        relative = item.get("path")
        if not _is_safe_bundle_relative_path(relative):
            errors.append(f"repo-assets.manifest.json contains unsafe asset path: {relative!r}")
            continue
        relative_str = str(relative)
        if relative_str in by_path:
            errors.append(f"repo-assets.manifest.json contains duplicate asset path: {relative_str}")
        by_path[relative_str] = item

        if item.get("exists") is not True:
            errors.append(f"repo-assets.manifest.json marks required asset as missing: {relative_str}")
        if not _is_valid_sha256(item.get("sha256")):
            errors.append(f"repo-assets.manifest.json asset sha256 is invalid: {relative_str}")
        size = item.get("size_bytes")
        if not isinstance(size, int) or size < 0:
            errors.append(f"repo-assets.manifest.json asset size_bytes is invalid: {relative_str}")

    for relative in _REQUIRED_REPO_ASSETS:
        if relative not in by_path:
            errors.append(f"required repo asset missing from repo-assets.manifest.json: {relative}")

    return errors


def _verify_generated_command_modes(out: Path) -> list[str]:
    errors: list[str] = []
    if os.name == "nt":
        # Windows does not surface POSIX executable bits the way Linux bundle targets do.
        # Generated helpers are still chmod 755 on Unix; CI and the target host enforce this.
        return errors
    for relative in _REQUIRED_GENERATED_FILES:
        if not relative.startswith("commands/"):
            continue
        path = out / relative
        if path.exists() and not (path.stat().st_mode & 0o111):
            errors.append(f"generated command is not executable: {relative}")
    return errors


_GENERATED_DOCKER_HARDENING_EXPECTED_COUNTS = {
    "docker-compose.single-tenant.yml": {
        "read_only: true": 1,
        "cap_drop:": 1,
        "no-new-privileges:true": 1,
        "/tmp:rw,nosuid,nodev,noexec,size=64m": 1,
    },
    "systemd/strategy-validator.service": {
        "--read-only": 2,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 2,
        "--cap-drop ALL": 2,
        "--security-opt no-new-privileges:true": 2,
    },
    "commands/compose-up.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/preflight.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/verify-ledger.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/backup-ledger.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/restore-ledger.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/acceptance.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
    "commands/post-deploy-evidence.sh": {
        "--read-only": 1,
        "--tmpfs /tmp:rw,nosuid,nodev,noexec,size=64m": 1,
        "--cap-drop ALL": 1,
        "--security-opt no-new-privileges:true": 1,
    },
}


def _verify_generated_docker_hardening_counts(out: Path) -> list[str]:
    """Reject generated runtime helper drift in Docker hardening flags.

    These counts intentionally mirror the generated single-tenant envelope: one
    hardened container invocation for most helpers, two in systemd (the pre-start
    env validator and the long-lived API container), and one Compose service
    profile.  This catches copy/paste drift such as duplicated tmpfs flags or
    accidentally removed no-new-privileges guards even when the manifest digest
    inventory was regenerated from the drifted files.
    """

    errors: list[str] = []
    for relative, expected_counts in _GENERATED_DOCKER_HARDENING_EXPECTED_COUNTS.items():
        path = out / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for token, expected_count in expected_counts.items():
            actual_count = text.count(token)
            if actual_count != expected_count:
                errors.append(
                    "generated Docker hardening drift: "
                    f"{relative} token={token!r} expected_count={expected_count} actual_count={actual_count}"
                )
    return errors


def _verify_generated_compose_runtime_contract(out: Path) -> list[str]:
    """Reject Compose/helper drift that can make helpers touch a different runtime state.

    Compose normally prefixes named volumes with the project name unless each
    top-level volume has an explicit ``name``.  The generated helper containers
    use literal Docker volume names, so the Compose file must pin those names
    exactly once.  This structural check catches duplicate or missing volume
    declarations even if a generated manifest has already been refreshed.
    """

    path = out / "docker-compose.single-tenant.yml"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    expected_tokens = {
        "service ledger volume binding": "      - strategy-validator-ledger:/var/lib/strategy-validator",
        "service backup volume binding": "      - strategy-validator-backups:/var/backups/strategy-validator",
        "pinned ledger volume name": "    name: strategy-validator-ledger",
        "pinned backup volume name": "    name: strategy-validator-backups",
        "Compose runtime env file": "      - ${STRATEGY_VALIDATOR_COMPOSE_ENV_FILE:-./deployment.env}",
        "host port bind": '      - "127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT:-8000}:8000"',
    }
    errors: list[str] = []
    for label, token in expected_tokens.items():
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated Compose runtime contract drift: "
                f"{label} expected_count=1 actual_count={actual_count}"
            )

    # Guard the top-level volume keys separately from service volume references.
    for volume_name in ("strategy-validator-ledger", "strategy-validator-backups"):
        token = f"  {volume_name}:\n    name: {volume_name}"
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated Compose runtime contract drift: "
                f"top-level {volume_name} declaration expected_count=1 actual_count={actual_count}"
            )
    return errors




def _verify_generated_compose_lifecycle_contract(out: Path) -> list[str]:
    """Reject Compose helper drift that would ignore deployment.env interpolation.

    Docker Compose does not use a service ``env_file`` as an interpolation
    source for the ``ports`` stanza.  The generated lifecycle helper must pass
    the operator env file with ``--env-file`` when running Compose, otherwise a
    non-default ``STRATEGY_VALIDATOR_HOST_PORT`` stored only in deployment.env
    can be silently ignored.
    """

    errors: list[str] = []
    up_path = out / "commands/compose-up.sh"
    if up_path.exists():
        text = up_path.read_text(encoding="utf-8")
        expected_tokens = {
            "bundle-local env default": "STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env",
            "bundle-local Compose default": "STRATEGY_VALIDATOR_COMPOSE_FILE:=${BUNDLE_DIR}/docker-compose.single-tenant.yml",
            "env file canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "Compose file canonicalization": "STRATEGY_VALIDATOR_COMPOSE_FILE=\"${HOST_COMPOSE_DIR}/${HOST_COMPOSE_BASENAME}\"",
            "preflight env validator": "strategy-validator-deployment-env-check \"/deployment-env/${HOST_ENV_BASENAME}\" --require-valid --json",
            "Compose env interpolation file": "--env-file \"${STRATEGY_VALIDATOR_ENV_FILE}\"",
            "Compose runtime env export": "export STRATEGY_VALIDATOR_COMPOSE_ENV_FILE=\"${STRATEGY_VALIDATOR_ENV_FILE}\"",
            "Compose file argument": "  -f \"${STRATEGY_VALIDATOR_COMPOSE_FILE}\" \\",
            "Compose up action": "up -d",
        }
        for label, token in expected_tokens.items():
            actual_count = text.count(token)
            if actual_count != 1:
                errors.append(
                    "generated Compose lifecycle contract drift: "
                    f"compose-up {label} expected_count=1 actual_count={actual_count}"
                )

    down_path = out / "commands/compose-down.sh"
    if down_path.exists():
        text = down_path.read_text(encoding="utf-8")
        expected_tokens = {
            "bundle-local env default": "STRATEGY_VALIDATOR_ENV_FILE:=${BUNDLE_DIR}/deployment.env",
            "bundle-local Compose default": "STRATEGY_VALIDATOR_COMPOSE_FILE:=${BUNDLE_DIR}/docker-compose.single-tenant.yml",
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env file canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
            "Compose file canonicalization": "STRATEGY_VALIDATOR_COMPOSE_FILE=\"${HOST_COMPOSE_DIR}/${HOST_COMPOSE_BASENAME}\"",
            "Compose env interpolation file": "--env-file \"${STRATEGY_VALIDATOR_ENV_FILE}\"",
            "Compose runtime env export": "export STRATEGY_VALIDATOR_COMPOSE_ENV_FILE=\"${STRATEGY_VALIDATOR_ENV_FILE}\"",
            "Compose file argument": "  -f \"${STRATEGY_VALIDATOR_COMPOSE_FILE}\" \\",
            "Compose down action": "down",
        }
        for label, token in expected_tokens.items():
            actual_count = text.count(token)
            if actual_count != 1:
                errors.append(
                    "generated Compose lifecycle contract drift: "
                    f"compose-down {label} expected_count=1 actual_count={actual_count}"
                )


    return errors


def _verify_generated_helper_env_path_contract(out: Path) -> list[str]:
    """Reject helper drift that makes Docker/env readers use caller-relative env paths.

    Generated helpers self-locate bundle defaults, but operators may override
    ``STRATEGY_VALIDATOR_ENV_FILE``.  Every helper that passes that file to
    Docker or a smoke/evidence runner must canonicalize it before use so the
    validated env file, Docker ``--env-file`` source, and child helper env are
    the same absolute host path regardless of the caller's current directory.
    """

    helper_contracts: dict[str, dict[str, str]] = {
        "commands/api-smoke.sh": {
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/acceptance.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/preflight.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/verify-ledger.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/backup-ledger.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/restore-ledger.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
        "commands/post-deploy-evidence.sh": {
            "required env-file guard": "if [[ ! -f \"${STRATEGY_VALIDATOR_ENV_FILE}\" ]]; then",
            "env dir canonicalization": "HOST_ENV_DIR=\"$(cd \"$(dirname \"${STRATEGY_VALIDATOR_ENV_FILE}\")\" && pwd)\"",
            "env basename canonicalization": "HOST_ENV_BASENAME=\"$(basename \"${STRATEGY_VALIDATOR_ENV_FILE}\")\"",
            "env path canonicalization": "STRATEGY_VALIDATOR_ENV_FILE=\"${HOST_ENV_DIR}/${HOST_ENV_BASENAME}\"",
            "env export": "export STRATEGY_VALIDATOR_ENV_FILE",
        },
    }

    errors: list[str] = []
    for relative, expected_tokens in helper_contracts.items():
        path = out / relative
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for label, token in expected_tokens.items():
            actual_count = text.count(token)
            if actual_count != 1:
                errors.append(
                    "generated helper env path contract drift: "
                    f"{relative} {label} expected_count=1 actual_count={actual_count}"
                )
    return errors


def _verify_generated_evidence_mount_contract(out: Path) -> list[str]:
    """Reject post-deploy evidence Docker fallback drift in mount mutability.

    The generated evidence collector only needs write access to the dedicated
    evidence directory.  The deployment bundle, repo root, and env directory are
    evidence inputs and must remain read-only inside fallback containers so a
    post-deploy collection run cannot mutate the handoff bundle or source files.
    """

    path = out / "commands/post-deploy-evidence.sh"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    expected_tokens = {
        "bundle input mount is read-only": "-v \"${HOST_BUNDLE_DIR}:${CONTAINER_BUNDLE_DIR}:ro\"",
        "repo input mount is read-only": "-v \"${HOST_REPO_ROOT}:${CONTAINER_REPO_ROOT}:ro\"",
        "env input mount is read-only": "-v \"${HOST_ENV_DIR}:/env:ro\"",
        "evidence output mount is read-write": "-v \"${HOST_EVIDENCE_DIR}:${CONTAINER_EVIDENCE_DIR}:rw\"",
    }
    forbidden_tokens = {
        "bundle input mounted read-write": "-v \"${HOST_BUNDLE_DIR}:${CONTAINER_BUNDLE_DIR}:rw\"",
        "repo input mounted read-write": "-v \"${HOST_REPO_ROOT}:${CONTAINER_REPO_ROOT}:rw\"",
        "env input mounted read-write": "-v \"${HOST_ENV_DIR}:/env:rw\"",
        "evidence output mounted read-only": "-v \"${HOST_EVIDENCE_DIR}:${CONTAINER_EVIDENCE_DIR}:ro\"",
    }
    errors: list[str] = []
    for label, token in expected_tokens.items():
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated evidence mount contract drift: "
                f"{label} expected_count=1 actual_count={actual_count}"
            )
    for label, token in forbidden_tokens.items():
        actual_count = text.count(token)
        if actual_count:
            errors.append(
                "generated evidence mount contract drift: "
                f"{label} forbidden_count={actual_count}"
            )
    return errors


def _verify_generated_restore_breakglass_contract(out: Path) -> list[str]:
    """Reject restore-helper drift that can restore from the wrong filesystem.

    The generated restore helper runs inside a hardened container with only the
    named backup volume mounted at ``/var/backups/strategy-validator``. Operators
    must therefore provide a container-visible backup artifact under that root,
    not a host-local path that is invisible to the helper container. The helper
    also writes the pre-restore displaced-ledger copy under the same backup root
    so rollback evidence stays on durable backup storage.
    """

    path = out / "commands/restore-ledger.sh"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    expected_tokens = {
        "backup root declaration": 'BACKUP_ROOT="/var/backups/strategy-validator"',
        "backup path root/suffix guard": 'if [[ "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}" != "${BACKUP_ROOT}/"* || "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}" != *.sqlite3 ]]; then',
        "backup path refusal message": "STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH must be a container-visible .sqlite3 path under ${BACKUP_ROOT}",
        "pre-restore backup root guard": 'if [[ "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}" != "${BACKUP_ROOT}" && "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}" != "${BACKUP_ROOT}/"* ]]; then',
        "pre-restore backup refusal message": "STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR must be under ${BACKUP_ROOT}",
        "restore backup arg": '--backup-path "${STRATEGY_VALIDATOR_LEDGER_BACKUP_PATH}"',
        "pre-restore backup arg": '--pre-restore-backup-dir "${STRATEGY_VALIDATOR_PRE_RESTORE_BACKUP_DIR}"',
    }
    errors: list[str] = []
    for label, token in expected_tokens.items():
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated restore breakglass contract drift: "
                f"{label} expected_count=1 actual_count={actual_count}"
            )
    return errors


def _verify_generated_post_deploy_path_contract(out: Path) -> list[str]:
    """Reject evidence helper drift that uses caller-relative host paths.

    Post-deploy evidence is the final handoff record.  It must canonicalize the
    bundle, repo root, env file, and evidence directory once, export those
    absolute host paths, and use them consistently for host-side CLI calls.  If
    custom relative paths are left caller-relative, a later child command can
    write/read evidence from a different location than the one mounted into
    Docker fallback containers.
    """

    path = out / "commands/post-deploy-evidence.sh"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    expected_tokens = {
        "bundle dir canonicalization": 'HOST_BUNDLE_DIR="$(cd "${STRATEGY_VALIDATOR_BUNDLE_DIR}" && pwd)"',
        "bundle dir reassignment": 'STRATEGY_VALIDATOR_BUNDLE_DIR="${HOST_BUNDLE_DIR}"',
        "bundle dir export": 'export STRATEGY_VALIDATOR_BUNDLE_DIR',
        "repo root canonicalization": 'HOST_REPO_ROOT="$(cd "${STRATEGY_VALIDATOR_REPO_ROOT}" && pwd)"',
        "repo root reassignment": 'STRATEGY_VALIDATOR_REPO_ROOT="${HOST_REPO_ROOT}"',
        "repo root export": 'export STRATEGY_VALIDATOR_REPO_ROOT',
        "evidence dir canonicalization": 'HOST_EVIDENCE_DIR="$(cd "${STRATEGY_VALIDATOR_EVIDENCE_DIR}" && pwd)"',
        "evidence dir reassignment": 'STRATEGY_VALIDATOR_EVIDENCE_DIR="${HOST_EVIDENCE_DIR}"',
        "evidence dir export": 'export STRATEGY_VALIDATOR_EVIDENCE_DIR',
        "host bundle args use canonical bundle dir": '--output-dir "${STRATEGY_VALIDATOR_BUNDLE_DIR}" --check --require-ready --json',
        "host acceptance bundle arg uses canonical bundle dir": '--bundle-dir "${STRATEGY_VALIDATOR_BUNDLE_DIR}"',
        "host evidence output uses canonical evidence dir": '--manifest-output-path "${STRATEGY_VALIDATOR_EVIDENCE_DIR}/deployment-evidence.json"',
    }
    errors: list[str] = []
    for label, token in expected_tokens.items():
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated post-deploy path contract drift: "
                f"{label} expected_count=1 actual_count={actual_count}"
            )
    return errors


def _verify_generated_systemd_runtime_contract(out: Path) -> list[str]:
    """Reject systemd runtime drift that can bypass the single-tenant envelope.

    The systemd unit is a generated deployment contract, not just a convenience
    snippet.  Digest checks catch local edits, but a regenerated manifest from a
    drifted template would otherwise still pass.  These structural checks make
    the same runtime invariants deployment-blocking for systemd that Compose
    already receives: loopback-only host binding, explicit env validation before
    destructive cleanup, and helper/API containers using the expected durable
    volumes.
    """

    path = out / "systemd/strategy-validator.service"
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8")
    expected_tokens = {
        "host port default": "Environment=STRATEGY_VALIDATOR_HOST_PORT=8000",
        "deployment env file": "EnvironmentFile=/etc/strategy-validator/deployment.env",
        "pre-start env-check container": "ExecStartPre=/usr/bin/docker run --rm --user 0:0 \\",
        "pre-start env-check command": "strategy-validator-deployment-env-check /deployment-env/deployment.env --require-valid --json",
        "ignored stale container cleanup": "ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api",
        "api container start": "ExecStart=/usr/bin/docker run --rm --name strategy-validator-api \\",
        "ignored stop": "ExecStop=-/usr/bin/docker stop strategy-validator-api",
        "loopback host port bind": "  -p 127.0.0.1:${STRATEGY_VALIDATOR_HOST_PORT}:8000 \\",
        "deployment env mount": "  -v /etc/strategy-validator:/deployment-env:ro \\",
        "ledger volume mount": "  -v strategy-validator-ledger:/var/lib/strategy-validator \\",
        "backup volume mount": "  -v strategy-validator-backups:/var/backups/strategy-validator \\",
    }

    errors: list[str] = []
    for label, token in expected_tokens.items():
        actual_count = text.count(token)
        if actual_count != 1:
            errors.append(
                "generated systemd runtime contract drift: "
                f"{label} expected_count=1 actual_count={actual_count}"
            )

    forbidden_tokens = {
        "non-ignored stale cleanup": "ExecStartPre=/usr/bin/docker rm -f strategy-validator-api",
        "non-ignored stop": "ExecStop=/usr/bin/docker stop strategy-validator-api",
        "hard-coded default port bind": "  -p 127.0.0.1:8000:8000 \\",
        "non-loopback default bind": "  -p 0.0.0.0:8000:8000 \\",
    }
    for label, token in forbidden_tokens.items():
        actual_count = text.count(token)
        if actual_count:
            errors.append(
                "generated systemd runtime contract drift: "
                f"{label} forbidden_count={actual_count}"
            )

    env_check_marker = "strategy-validator-deployment-env-check /deployment-env/deployment.env --require-valid --json"
    cleanup_marker = "ExecStartPre=-/usr/bin/docker rm -f strategy-validator-api"
    api_start_marker = "ExecStart=/usr/bin/docker run --rm --name strategy-validator-api"
    if all(marker in text for marker in (env_check_marker, cleanup_marker, api_start_marker)):
        if not (text.index(env_check_marker) < text.index(cleanup_marker) < text.index(api_start_marker)):
            errors.append(
                "generated systemd runtime contract drift: "
                "expected env validation before stale-container cleanup before API start"
            )
    return errors


def _collect_generated_files(output_dir: Path) -> tuple[GeneratedFile, ...]:
    files: list[GeneratedFile] = []
    for relative in _REQUIRED_GENERATED_FILES:
        path = output_dir / relative
        if not path.exists():
            continue
        files.append(
            GeneratedFile(
                path=relative,
                sha256=_sha256_file(path),
                size_bytes=path.stat().st_size,
            )
        )
    return tuple(files)


def build_single_tenant_deployment_bundle(
    *,
    env_file: str | Path = "deployment.env",
    output_dir: str | Path = _DEFAULT_OUTPUT_DIR,
    repo_root: str | Path = ".",
    force: bool = False,
) -> DeploymentBundleReport:
    """Generate a secret-safe backend-only deployment bundle."""

    env_path = Path(env_file).expanduser().resolve()
    out = Path(output_dir).expanduser().resolve()
    repo = Path(repo_root).expanduser().resolve()
    errors: list[str] = []

    if out.exists() and any(out.iterdir()) and not force:
        errors.append(f"output directory is not empty; pass --force to replace generated files: {out}")
        env_check = build_single_tenant_deployment_env_check(env_path)
        return DeploymentBundleReport(
            schema_version=_SCHEMA_VERSION,
            ok=False,
            output_dir=str(out),
            env_file=str(env_path),
            generated_at_utc=datetime.now(timezone.utc).isoformat(),
            deployment_model="single_tenant_backend_only",
            frontend_expected_package=_FRONTEND_PACKAGE,
            frontend_package_present=(repo / _FRONTEND_PACKAGE / "package.json").exists(),
            frontend_readiness_claimed=False,
            env_check_ok=env_check.ok,
            generated_files=_collect_generated_files(out) if out.exists() else (),
            errors=tuple(errors),
        )

    env_check = build_single_tenant_deployment_env_check(env_path)
    out.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    redacted_payload = _redacted_env_payload(env_path, env_check)

    repo_asset_payload = _repo_asset_manifest(repo, generated_at_utc=generated_at)
    repo_asset_errors = [
        "required repo asset missing at bundle generation: " + path
        for path in repo_asset_payload.get("missing_assets", [])
    ]

    _atomic_write_text(out / "deployment.env.redacted.json", json.dumps(redacted_payload, indent=2, sort_keys=True) + "\n")
    _atomic_write_text(out / "repo-assets.manifest.json", json.dumps(repo_asset_payload, indent=2, sort_keys=True) + "\n")
    _atomic_write_text(out / ".gitignore", _bundle_gitignore())
    _atomic_write_text(out / "docker-compose.single-tenant.yml", _compose_template())
    _atomic_write_text(out / "systemd/strategy-validator.service", _systemd_template())
    _atomic_write_text(out / "commands/compose-up.sh", _compose_up_script(), executable=True)
    _atomic_write_text(out / "commands/compose-down.sh", _compose_down_script(), executable=True)
    _atomic_write_text(out / "commands/preflight.sh", _preflight_script(), executable=True)
    _atomic_write_text(out / "commands/api-smoke.sh", _api_smoke_script(), executable=True)
    _atomic_write_text(out / "commands/api-smoke.py", _api_smoke_python_script(), executable=True)
    _atomic_write_text(out / "commands/verify-ledger.sh", _verify_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/backup-ledger.sh", _backup_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/restore-ledger.sh", _restore_ledger_script(), executable=True)
    _atomic_write_text(out / "commands/acceptance.sh", _acceptance_script(), executable=True)
    _atomic_write_text(out / "commands/post-deploy-evidence.sh", _post_deploy_evidence_script(), executable=True)
    _atomic_write_text(out / "README.md", _readme(env_check))

    frontend_present = (repo / _FRONTEND_PACKAGE / "package.json").exists()
    # Write a preliminary manifest without its own digest, then rewrite with the
    # final generated file list excluding manifest self-reference instability.
    preliminary_files = _collect_generated_files(out)
    manifest_without_self = {
        "schema_version": _SCHEMA_VERSION,
        "ok": bool(env_check.ok),
        "generated_at_utc": generated_at,
        "deployment_model": "single_tenant_backend_only",
        "frontend_expected_package": _FRONTEND_PACKAGE,
        "frontend_package_present": frontend_present,
        "frontend_readiness_claimed": False,
        "env_file": str(env_path),
        "env_check_ok": env_check.ok,
        "generated_files": [asdict(item) for item in preliminary_files if item.path != "manifest.json"],
        "repo_assets_manifest_schema_version": _REPO_ASSET_SCHEMA_VERSION,
        "repo_asset_manifest_ok": not repo_asset_errors,
        "errors": (repo_asset_errors + ([] if env_check.ok else ["deployment env check has ERROR issues; inspect deployment.env.redacted.json"])),
    }
    _atomic_write_text(out / "manifest.json", json.dumps(manifest_without_self, indent=2, sort_keys=True) + "\n")

    generated_files = _collect_generated_files(out)
    report_errors = repo_asset_errors + ([] if env_check.ok else ["deployment env check has ERROR issues; inspect deployment.env.redacted.json"])
    return DeploymentBundleReport(
        schema_version=_SCHEMA_VERSION,
        ok=bool(env_check.ok and not report_errors),
        output_dir=str(out),
        env_file=str(env_path),
        generated_at_utc=generated_at,
        deployment_model="single_tenant_backend_only",
        frontend_expected_package=_FRONTEND_PACKAGE,
        frontend_package_present=frontend_present,
        frontend_readiness_claimed=False,
        env_check_ok=env_check.ok,
        generated_files=generated_files,
        errors=tuple(report_errors),
    )


def check_single_tenant_deployment_bundle(output_dir: str | Path) -> DeploymentBundleReport:
    """Check that a generated bundle has the expected files and schema."""

    out = Path(output_dir).expanduser().resolve()
    errors: list[str] = []
    manifest_path = out / "manifest.json"
    manifest: dict[str, object] = {}
    if not manifest_path.exists():
        errors.append("manifest.json is missing")
    else:
        try:
            loaded = json.loads(manifest_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                manifest = loaded
            else:
                errors.append("manifest.json is not a JSON object")
        except json.JSONDecodeError as exc:
            errors.append(f"manifest.json is invalid JSON: {exc}")

    for relative in _REQUIRED_GENERATED_FILES:
        if not (out / relative).exists():
            errors.append(f"missing generated file: {relative}")

    if manifest.get("schema_version") not in {None, _SCHEMA_VERSION}:
        errors.append("manifest schema_version is not single_tenant_deployment_bundle/v1")
    if manifest and manifest.get("ok") is not True:
        errors.append("manifest ok field is not true; regenerate the bundle after fixing deployment readiness issues")
    if manifest and manifest.get("deployment_model") != "single_tenant_backend_only":
        errors.append("manifest deployment_model is not single_tenant_backend_only")
    if manifest and manifest.get("frontend_readiness_claimed") is not False:
        errors.append("manifest must not claim frontend readiness")
    if manifest:
        errors.extend(_verify_manifest_generated_file_digests(out, manifest))
    errors.extend(_verify_generated_command_modes(out))
    errors.extend(_verify_generated_docker_hardening_counts(out))
    errors.extend(_verify_generated_compose_runtime_contract(out))
    errors.extend(_verify_generated_compose_lifecycle_contract(out))
    errors.extend(_verify_generated_helper_env_path_contract(out))
    errors.extend(_verify_generated_evidence_mount_contract(out))
    errors.extend(_verify_generated_restore_breakglass_contract(out))
    errors.extend(_verify_generated_post_deploy_path_contract(out))
    errors.extend(_verify_generated_systemd_runtime_contract(out))

    repo_assets_path = out / "repo-assets.manifest.json"
    if repo_assets_path.exists():
        try:
            repo_assets = json.loads(repo_assets_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"repo-assets.manifest.json is invalid JSON: {exc}")
        else:
            errors.extend(_verify_repo_asset_manifest_payload(repo_assets))

    generated_files = _collect_generated_files(out) if out.exists() else ()
    return DeploymentBundleReport(
        schema_version=_SCHEMA_VERSION,
        ok=not errors,
        output_dir=str(out),
        env_file=str(manifest.get("env_file", "")),
        generated_at_utc=str(manifest.get("generated_at_utc", "")),
        deployment_model=str(manifest.get("deployment_model", "single_tenant_backend_only")),
        frontend_expected_package=str(manifest.get("frontend_expected_package", _FRONTEND_PACKAGE)),
        frontend_package_present=bool(manifest.get("frontend_package_present", False)),
        frontend_readiness_claimed=bool(manifest.get("frontend_readiness_claimed", False)),
        env_check_ok=bool(manifest.get("env_check_ok", False)),
        generated_files=generated_files,
        errors=tuple(errors),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate/check a backend-only single-tenant deployment bundle.")
    parser.add_argument("--env-file", default="deployment.env", help="Operator deployment env file to validate and summarize.")
    parser.add_argument("--output-dir", default=_DEFAULT_OUTPUT_DIR, help="Directory where generated bundle files are written.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for frontend absence/readiness checks.")
    parser.add_argument("--force", action="store_true", help="Allow replacing generated files in a non-empty output directory.")
    parser.add_argument("--check", action="store_true", help="Check an existing generated bundle instead of generating one.")
    parser.add_argument("--require-ready", action="store_true", help="Exit non-zero unless the bundle/env is deployment-ready.")
    parser.add_argument("--json", action="store_true", help="Emit JSON. Plain output is JSON too for automation.")
    ns = parser.parse_args(argv)

    if ns.check:
        report = check_single_tenant_deployment_bundle(ns.output_dir)
    else:
        report = build_single_tenant_deployment_bundle(
            env_file=ns.env_file,
            output_dir=ns.output_dir,
            repo_root=ns.repo_root,
            force=ns.force,
        )
    sys.stdout.write(json.dumps(report.to_payload(), indent=2, sort_keys=True) + "\n")
    return 2 if ns.require_ready and not report.ok else 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
