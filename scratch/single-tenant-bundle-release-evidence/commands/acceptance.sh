#!/usr/bin/env bash
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
