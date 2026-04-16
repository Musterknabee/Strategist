from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.release_publication import publish_release_readiness_bundle
from strategy_validator.validator.services.integrity_gate_service import get_current_readiness


def get_readiness_health_payload() -> dict[str, Any]:
    """Return a transport-neutral readiness summary for API/CLI surfaces."""
    readiness = get_current_readiness()
    return {
        'ok': readiness.status == 'READY',
        'surface': 'readiness',
        'status': readiness.status,
        'adjudication_allowed': readiness.adjudication_allowed,
        'blocker_codes': [blocker.code for blocker in readiness.blockers],
    }


def publish_release_bundle_from_paths(
    *,
    policy_path: str | Path,
    keyed_host_fingerprint_path: str | Path,
    publication_path: str | Path,
    scope: str = 'FULL',
    burnin_artifact_paths: list[str | Path] | None = None,
) -> dict[str, object]:
    return publish_release_readiness_bundle(
        policy_path=Path(policy_path),
        keyed_host_fingerprint_path=Path(keyed_host_fingerprint_path),
        burnin_artifact_paths=[Path(item) for item in (burnin_artifact_paths or [])],
        scope=scope,
        publication_path=Path(publication_path),
    )
