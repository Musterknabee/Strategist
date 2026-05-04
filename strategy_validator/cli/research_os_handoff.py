"""CLI for Research OS single-tenant handoff packs."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_handoff_ops import (
    build_and_write_research_os_handoff_pack,
    build_research_os_handoff_pack,
    load_latest_research_os_handoff_pack,
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
    parser = argparse.ArgumentParser(description="Build/read Research OS single-tenant handoff packs.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build and write the latest handoff pack")
    _add_common(build)
    build.add_argument("--handoff-id", default="research-os-handoff")
    build.add_argument("--overwrite", action="store_true")

    preview = sub.add_parser("preview", help="Build the handoff pack without writing it")
    _add_common(preview)
    preview.add_argument("--handoff-id", default="research-os-handoff-preview")

    latest = sub.add_parser("latest", help="Read the latest handoff pack")
    _add_common(latest)

    args = parser.parse_args(argv)
    artifact_root = Path(args.artifact_root)

    if args.command == "build":
        pack, path = build_and_write_research_os_handoff_pack(
            artifact_root=artifact_root,
            handoff_id=args.handoff_id,
            overwrite=bool(args.overwrite),
        )
        payload = pack.model_dump(mode="json")
        payload["artifact_path"] = str(path)
        _print(payload, as_json=bool(args.json))
        return 0 if pack.status.value not in {"BLOCKED"} else 2

    if args.command == "preview":
        pack = build_research_os_handoff_pack(artifact_root=artifact_root, handoff_id=args.handoff_id)
        _print(pack.model_dump(mode="json"), as_json=bool(args.json))
        return 0

    if args.command == "latest":
        pack = load_latest_research_os_handoff_pack(artifact_root=artifact_root)
        if pack is None:
            _print({"ok": False, "status": "MISSING", "error": "NO_RESEARCH_OS_HANDOFF_PACK"}, as_json=bool(args.json))
            return 1
        _print(pack.model_dump(mode="json"), as_json=bool(args.json))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
