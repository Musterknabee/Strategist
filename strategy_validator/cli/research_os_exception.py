"""CLI for Research OS governed exception records."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from strategy_validator.application.research_os_exception_ops import (
    build_and_write_research_os_exception_record,
    build_research_os_exception_record,
    load_latest_research_os_exception_record,
)


def _print(payload: object) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build/read Research OS governed exception records.")
    sub = parser.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("request", help="Create a governed exception from the latest policy gate.")
    r.add_argument("--exception-id", default="research-os-exception-demo")
    r.add_argument("--operator-id", default="local-operator")
    r.add_argument("--rationale", required=True)
    r.add_argument("--ttl-hours", type=int, default=24)
    r.add_argument("--expires-at-utc", default=None)
    r.add_argument("--constraint", action="append", default=[])
    r.add_argument("--covered-warning", action="append", default=[])
    r.add_argument("--artifact-root", default="artifacts")
    r.add_argument("--repo-root", default=".")
    r.add_argument("--overwrite", action="store_true")
    r.add_argument("--json", action="store_true")
    p = sub.add_parser("preview", help="Build and print an exception without writing it.")
    p.add_argument("--exception-id", default="research-os-exception-preview")
    p.add_argument("--operator-id", default="local-operator")
    p.add_argument("--rationale", required=True)
    p.add_argument("--ttl-hours", type=int, default=24)
    p.add_argument("--expires-at-utc", default=None)
    p.add_argument("--constraint", action="append", default=[])
    p.add_argument("--covered-warning", action="append", default=[])
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--json", action="store_true")
    l = sub.add_parser("latest", help="Read the latest exception record.")
    l.add_argument("--artifact-root", default="artifacts")
    l.add_argument("--repo-root", default=".")
    l.add_argument("--json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)
    repo_root = Path(ns.repo_root).resolve()
    artifact_root = Path(ns.artifact_root).resolve()
    try:
        if ns.cmd == "request":
            record, path = build_and_write_research_os_exception_record(
                exception_id=ns.exception_id,
                operator_id=ns.operator_id,
                rationale=ns.rationale,
                ttl_hours=ns.ttl_hours,
                expires_at_utc=ns.expires_at_utc,
                constraints=ns.constraint,
                covered_warnings=ns.covered_warning,
                repo_root=repo_root,
                artifact_root=artifact_root,
                overwrite=ns.overwrite,
            )
            payload = record.model_dump(mode="json")
            payload["written_path"] = str(path)
            _print(payload)
            return 0 if record.status.value in {"ACTIVE", "NOT_APPLICABLE"} else 2
        if ns.cmd == "preview":
            record = build_research_os_exception_record(
                exception_id=ns.exception_id,
                operator_id=ns.operator_id,
                rationale=ns.rationale,
                ttl_hours=ns.ttl_hours,
                expires_at_utc=ns.expires_at_utc,
                constraints=ns.constraint,
                covered_warnings=ns.covered_warning,
                repo_root=repo_root,
                artifact_root=artifact_root,
            )
            _print(record.model_dump(mode="json"))
            return 0 if record.status.value in {"ACTIVE", "NOT_APPLICABLE"} else 2
        if ns.cmd == "latest":
            record = load_latest_research_os_exception_record(repo_root=repo_root, artifact_root=artifact_root)
            if record is None:
                _print({"ok": False, "status": "NOT_PRESENT", "error": "NO_RESEARCH_OS_EXCEPTION_RECORD"})
                return 1
            _print(record.model_dump(mode="json"))
            return 0 if record.status.value in {"ACTIVE", "NOT_APPLICABLE"} else 2
    except Exception as exc:  # pragma: no cover - CLI guardrail
        _print({"ok": False, "error": type(exc).__name__, "message": str(exc)})
        return 1
    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
