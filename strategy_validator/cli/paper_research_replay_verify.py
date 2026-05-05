"""Verify paper-research replay manifests offline (no network, no key requirement)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application.paper_research_replay import discover_replay_manifest_path, verify_replay_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-manifest", type=Path, default=None, help="Replay manifest JSON path.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Repository root for relative-path resolution.")
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=None,
        help="Allowed artifact root for replay path verification (defaults to repo root).",
    )
    parser.add_argument(
        "--allow-absolute-paths",
        action="store_true",
        help="Allow absolute artifact paths (still must remain under allowed artifact root).",
    )
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON summary.")
    ns = parser.parse_args(argv)

    replay_manifest = discover_replay_manifest_path(
        repo_root=ns.repo_root,
        replay_manifest_path=ns.replay_manifest,
        artifact_root=ns.artifact_root,
    )
    assert replay_manifest is not None
    summary = verify_replay_manifest(
        replay_manifest,
        repo_root=ns.repo_root,
        artifact_root=ns.artifact_root,
        allow_absolute_paths=ns.allow_absolute_paths,
    )
    payload = summary.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True))
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
