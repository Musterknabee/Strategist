from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.core.path_guards import resolve_within_root


def resolve_release_publication_paths(
    *,
    artifact_root: str | Path,
    policy_path: str | Path,
    keyed_host_fingerprint_path: str | Path,
    publication_path: str | Path,
    burnin_artifact_paths: list[str | Path] | None = None,
) -> dict[str, Any]:
    """Resolve release-publication paths under an explicit artifact root.

    Release publication must not infer trust boundaries from operator-supplied
    filenames. All inputs and outputs are constrained to ``artifact_root``
    before the bundle builder reads or writes the filesystem.
    """
    root = Path(artifact_root).expanduser().resolve()
    return {
        'artifact_root': root,
        'policy_path': resolve_within_root(policy_path, root=root, label='policy_path'),
        'keyed_host_fingerprint_path': resolve_within_root(
            keyed_host_fingerprint_path,
            root=root,
            label='keyed_host_fingerprint_path',
        ),
        'publication_path': resolve_within_root(publication_path, root=root, label='publication_path'),
        'burnin_artifact_paths': [
            resolve_within_root(path, root=root, label='burnin_artifact_path')
            for path in (burnin_artifact_paths or [])
        ],
    }


__all__ = ['resolve_release_publication_paths']
