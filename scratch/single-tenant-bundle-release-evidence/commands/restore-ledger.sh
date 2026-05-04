#!/usr/bin/env bash
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
