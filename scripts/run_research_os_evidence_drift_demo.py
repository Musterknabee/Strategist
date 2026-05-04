#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from strategy_validator.application.research_os_drift_ops import build_and_write_research_os_evidence_drift_report


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Build a Research OS evidence drift demo report")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--drift-id", default="evidence-drift-demo")
    p.add_argument("--baseline-catalog", default=None)
    p.add_argument("--candidate-catalog", default=None)
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)
    report, path = build_and_write_research_os_evidence_drift_report(
        drift_id=ns.drift_id,
        artifact_root=Path(ns.artifact_root),
        baseline_catalog_path=Path(ns.baseline_catalog).resolve() if ns.baseline_catalog else None,
        candidate_catalog_path=Path(ns.candidate_catalog).resolve() if ns.candidate_catalog else None,
        overwrite=ns.overwrite,
    )
    payload = {
        "ok": report.status.value not in {"BLOCKED", "EMPTY"},
        "status": report.status.value,
        "trust_banner": report.trust_banner.value,
        "manifest_path": str(path),
        "added_count": report.added_count,
        "removed_count": report.removed_count,
        "changed_count": report.changed_count,
        "unchanged_count": report.unchanged_count,
        "warnings": report.warnings,
        "blockers": report.blockers,
        "no_live_trading": report.no_live_trading,
        "no_broker_orders": report.no_broker_orders,
        "no_order_controls": report.no_order_controls,
    }
    if ns.json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        print(payload, flush=True)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
