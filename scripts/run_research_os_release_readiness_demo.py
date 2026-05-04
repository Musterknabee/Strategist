#!/usr/bin/env python3
"""Build a Research OS release-readiness report demo artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_release_readiness_ops import build_and_write_research_os_release_readiness_report


def main() -> int:
    p = argparse.ArgumentParser(description="Run the Research OS release-readiness demo.")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--repo-root", default=".")
    p.add_argument("--report-id", default="release-readiness-demo")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report, path = build_and_write_research_os_release_readiness_report(
        artifact_root=Path(args.artifact_root).resolve(),
        repo_root=Path(args.repo_root).resolve(),
        report_id=args.report_id,
        overwrite=args.overwrite,
    )
    payload = {
        "ok": True,
        "artifact_path": str(path),
        "report_id": report.report_id,
        "status": report.status.value,
        "decision": report.decision.value,
        "trust_banner": report.trust_banner.value,
        "release_review_ready": report.release_review_ready,
        "deployment_approved": report.deployment_approved,
        "blocker_count": len(report.blockers),
        "warning_count": len(report.warnings),
        "no_live_trading": report.no_live_trading,
        "no_broker_orders": report.no_broker_orders,
        "no_order_controls": report.no_order_controls,
        "deployment_approval_unchanged": report.deployment_approval_unchanged,
    }
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        print(payload, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
