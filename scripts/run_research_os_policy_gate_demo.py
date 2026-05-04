#!/usr/bin/env python3
"""Build a Research OS policy gate report for local operator/demo use."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_policy_gate_ops import build_and_write_research_os_policy_gate_report


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Research OS policy gate demo.")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--gate-id", default="policy-gate-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args()
    report, path = build_and_write_research_os_policy_gate_report(
        gate_id=ns.gate_id,
        repo_root=Path(ns.repo_root).resolve(),
        artifact_root=Path(ns.artifact_root).resolve(),
        overwrite=ns.overwrite,
    )
    payload = report.model_dump(mode="json")
    payload.update({
        "ok": report.decision.value in {"PASS", "WARN"},
        "written_path": str(path),
    })
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
