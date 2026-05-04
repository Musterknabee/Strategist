from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_drift_ops import (
    build_and_write_research_os_evidence_drift_report,
    build_ui_research_os_evidence_drift_latest_payload,
)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for k, v in payload.items():
            print(f"{k}: {v}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build/read the Research OS evidence drift report")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Compare evidence catalogs and write a drift report")
    b.add_argument("--drift-id", default="research-os-evidence-drift")
    b.add_argument("--artifact-root", default=None)
    b.add_argument("--repo-root", default=None)
    b.add_argument("--baseline-catalog", default=None)
    b.add_argument("--candidate-catalog", default=None)
    b.add_argument("--overwrite", action="store_true")
    b.add_argument("--json", action="store_true")

    l = sub.add_parser("latest", help="Print latest drift read-plane payload")
    l.add_argument("--artifact-root", default=None)
    l.add_argument("--repo-root", default=None)
    l.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)
    repo_root = Path(ns.repo_root).resolve() if getattr(ns, "repo_root", None) else None
    artifact_root = Path(ns.artifact_root).resolve() if getattr(ns, "artifact_root", None) else None
    try:
        if ns.cmd == "build":
            report, path = build_and_write_research_os_evidence_drift_report(
                drift_id=ns.drift_id,
                repo_root=repo_root,
                artifact_root=artifact_root,
                baseline_catalog_path=Path(ns.baseline_catalog).resolve() if ns.baseline_catalog else None,
                candidate_catalog_path=Path(ns.candidate_catalog).resolve() if ns.candidate_catalog else None,
                overwrite=ns.overwrite,
            )
            _emit(
                {
                    "ok": report.status.value not in {"BLOCKED", "EMPTY"},
                    "drift_id": report.drift_id,
                    "status": report.status.value,
                    "trust_banner": report.trust_banner.value,
                    "manifest_path": str(path),
                    "baseline_catalog_id": report.baseline_catalog_id,
                    "candidate_catalog_id": report.candidate_catalog_id,
                    "added_count": report.added_count,
                    "removed_count": report.removed_count,
                    "changed_count": report.changed_count,
                    "unchanged_count": report.unchanged_count,
                    "total_compared_count": report.total_compared_count,
                    "warnings": report.warnings,
                    "blockers": report.blockers,
                    "drift_spine_sha256": report.drift_spine_sha256,
                    "manifest_sha256": report.manifest_sha256,
                    "no_live_trading": report.no_live_trading,
                    "no_broker_orders": report.no_broker_orders,
                    "no_order_controls": report.no_order_controls,
                    "deployment_approval_unchanged": report.deployment_approval_unchanged,
                },
                as_json=ns.json,
            )
            return 0 if report.status.value not in {"BLOCKED", "EMPTY"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_evidence_drift_latest_payload(repo_root=repo_root, artifact_root=artifact_root), as_json=ns.json)
            return 0
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
