#!/usr/bin/env python3
"""Build a Research OS remediation plan from existing local artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_remediation_ops import build_and_write_research_os_remediation_plan


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a Research OS remediation demo.")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--plan-id", default="research-os-remediation-demo")
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args()
    plan, path = build_and_write_research_os_remediation_plan(
        plan_id=ns.plan_id,
        repo_root=Path(ns.repo_root).resolve(),
        artifact_root=Path(ns.artifact_root).resolve(),
        overwrite=ns.overwrite,
    )
    payload = {
        "ok": plan.status.value in {"READY", "RESTRICTED"},
        "status": plan.status.value,
        "trust_banner": plan.trust_banner.value,
        "plan_id": plan.plan_id,
        "item_count": plan.item_count,
        "open_count": plan.open_count,
        "blocked_count": plan.blocked_count,
        "waived_count": plan.waived_count,
        "written_path": str(path),
        "manifest_sha256": plan.manifest_sha256,
        "no_live_trading": plan.no_live_trading,
        "no_broker_orders": plan.no_broker_orders,
        "no_order_controls": plan.no_order_controls,
    }
    print(json.dumps(payload if ns.json else plan.model_dump(mode="json"), indent=2, sort_keys=True, default=str))
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
