#!/usr/bin/env python3
"""Build a demo Research OS governed exception record from latest policy gate."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_exception_ops import build_and_write_research_os_exception_record


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Research OS exception demo.")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--exception-id", default="research-os-exception-demo")
    parser.add_argument("--operator-id", default="local-operator")
    parser.add_argument("--rationale", default="Time-bounded review of restricted paper-only Research OS evidence; not deployment approval.")
    parser.add_argument("--ttl-hours", type=int, default=24)
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args()
    record, path = build_and_write_research_os_exception_record(
        exception_id=ns.exception_id,
        operator_id=ns.operator_id,
        rationale=ns.rationale,
        ttl_hours=ns.ttl_hours,
        repo_root=Path.cwd(),
        artifact_root=Path(ns.artifact_root),
        overwrite=ns.overwrite,
    )
    payload = record.model_dump(mode="json")
    payload.update({"ok": record.status.value in {"ACTIVE", "NOT_APPLICABLE"}, "written_path": str(path)})
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
