"""CLI for Research OS review journal artifacts."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_review_journal_ops import (
    build_and_write_research_os_review_journal,
    build_research_os_review_journal,
    load_latest_research_os_review_journal,
)


def _print(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str), flush=True)
    else:
        print(payload, flush=True)


def _add_common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--json", action="store_true")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build/read Research OS review journal artifacts.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build and write a review journal from latest Research OS review artifacts")
    _add_common(build)
    build.add_argument("--journal-id", default="research-os-review-journal")
    build.add_argument("--overwrite", action="store_true")

    preview = sub.add_parser("preview", help="Build a review journal payload without writing it")
    _add_common(preview)
    preview.add_argument("--journal-id", default="research-os-review-journal-preview")

    latest = sub.add_parser("latest", help="Read latest review journal")
    _add_common(latest)

    args = parser.parse_args(argv)
    artifact_root = Path(args.artifact_root)

    if args.command == "build":
        journal, path = build_and_write_research_os_review_journal(
            journal_id=args.journal_id,
            artifact_root=artifact_root,
            overwrite=bool(args.overwrite),
        )
        payload = journal.model_dump(mode="json")
        payload["artifact_path"] = str(path)
        _print(payload, as_json=bool(args.json))
        return 0 if payload.get("status") in {"READY", "RESTRICTED"} else 2

    if args.command == "preview":
        journal = build_research_os_review_journal(journal_id=args.journal_id, artifact_root=artifact_root)
        _print(journal.model_dump(mode="json"), as_json=bool(args.json))
        return 0 if journal.status.value in {"READY", "RESTRICTED"} else 2

    if args.command == "latest":
        journal = load_latest_research_os_review_journal(artifact_root=artifact_root)
        payload = {"ok": journal is not None, "latest": journal.model_dump(mode="json") if journal is not None else None}
        _print(payload, as_json=bool(args.json))
        return 0 if journal is not None else 1

    parser.error("unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
