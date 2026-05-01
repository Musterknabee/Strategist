#!/usr/bin/env bash
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
