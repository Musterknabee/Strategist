"""CLI for Research OS release-readiness review reports."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_release_readiness_ops import (
    build_and_write_research_os_release_readiness_report,
    build_research_os_release_readiness_report,
    load_latest_research_os_release_readiness_report,
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
    parser = argparse.ArgumentParser(description="Build/read Research OS release-readiness review reports.")
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build", help="Build and write the latest release-readiness report")
    _add_common(build)
    build.add_argument("--report-id", default="research-os-release-readiness")
    build.add_argument("--overwrite", action="store_true")

    preview = sub.add_parser("preview", help="Build the release-readiness report without writing it")
    _add_common(preview)
    preview.add_argument("--report-id", default="research-os-release-readiness-preview")

    latest = sub.add_parser("latest", help="Read the latest release-readiness report")
    _add_common(latest)

    args = parser.parse_args(argv)
    artifact_root = Path(args.artifact_root)

    if args.command == "build":
        report, path = build_and_write_research_os_release_readiness_report(
            artifact_root=artifact_root,
            report_id=args.report_id,
            overwrite=bool(args.overwrite),
        )
        payload = report.model_dump(mode="json")
        payload["artifact_path"] = str(path)
        _print(payload, as_json=bool(args.json))
        return 0 if report.status.value != "BLOCKED" else 2

    if args.command == "preview":
        report = build_research_os_release_readiness_report(artifact_root=artifact_root, report_id=args.report_id)
        _print(report.model_dump(mode="json"), as_json=bool(args.json))
        return 0

    if args.command == "latest":
        report = load_latest_research_os_release_readiness_report(artifact_root=artifact_root)
        if report is None:
            _print({"ok": False, "status": "MISSING", "error": "NO_RESEARCH_OS_RELEASE_READINESS_REPORT"}, as_json=bool(args.json))
            return 1
        _print(report.model_dump(mode="json"), as_json=bool(args.json))
        return 0

    parser.error("unknown command")
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
