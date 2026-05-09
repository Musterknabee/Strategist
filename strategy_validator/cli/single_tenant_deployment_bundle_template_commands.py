"""Command helper templates for the single-tenant deployment bundle."""
from __future__ import annotations

from pathlib import Path

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

__all__ = (
    "_compose_up_script",
    "_compose_down_script",
    "_preflight_script",
    "_api_smoke_script",
    "_api_smoke_python_script",
    "_verify_ledger_script",
    "_backup_ledger_script",
    "_restore_ledger_script",
)
