"""Helper-script contract verification for generated single-tenant bundles."""
from __future__ import annotations

from pathlib import Path

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
