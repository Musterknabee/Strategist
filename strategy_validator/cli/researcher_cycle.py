"""Certification-only fixture: verify seeded researcher_cycle candidate queue exists."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--artifact-root",
        type=Path,
        required=True,
        help="Root directory where certification_stability seeded researcher_cycle/candidate_queue.json.",
    )
    parser.add_argument("--json", action="store_true", help="Emit a short JSON line to stdout.")
    ns = parser.parse_args(argv)
    root = ns.artifact_root.resolve()
    queue = root / "researcher_cycle" / "candidate_queue.json"
    if not queue.is_file():
        print(f"researcher_cycle: missing candidate queue at {queue}", file=sys.stderr)
        return 1
    try:
        payload = json.loads(queue.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        print(f"researcher_cycle: invalid JSON in {queue}: {exc}", file=sys.stderr)
        return 1
    if not isinstance(payload, dict):
        print("researcher_cycle: candidate queue must be a JSON object", file=sys.stderr)
        return 1
    if ns.json:
        print(
            json.dumps(
                {
                    "schema_version": "researcher_cycle_fixture_cli/v1",
                    "status": "PASS",
                    "candidate_queue_path": str(queue),
                    "repo_root": str(REPO_ROOT),
                },
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
