"""Runtime-envelope verification for generated single-tenant bundle files."""
from __future__ import annotations

from pathlib import Path

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
