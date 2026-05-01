#!/usr/bin/env bash
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
