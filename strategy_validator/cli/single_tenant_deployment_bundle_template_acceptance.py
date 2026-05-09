"""Acceptance and evidence helper templates for the single-tenant deployment bundle."""
from __future__ import annotations

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

__all__ = (
    "_acceptance_script",
    "_post_deploy_evidence_script",
)
