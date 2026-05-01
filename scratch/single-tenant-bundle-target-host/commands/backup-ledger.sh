#!/usr/bin/env bash
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
