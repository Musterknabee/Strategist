"""Verify paper-research replay manifests offline (no network, no key requirement)."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application.paper_research_replay import verify_replay_manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay-manifest", type=Path, required=True, help="Replay manifest JSON path.")
    parser.add_argument("--json", action="store_true", help="Pretty-print JSON summary.")
    ns = parser.parse_args(argv)

    summary = verify_replay_manifest(ns.replay_manifest, repo_root=Path.cwd())
    payload = summary.model_dump(mode="json")
    print(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True))
    return 0 if summary.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
