from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_operator_run_ops import (
    build_and_write_research_os_operator_run,
    build_ui_research_os_operator_run_latest_payload,
)
from strategy_validator.contracts.research_os_attestation import ResearchOsOperatorDecision


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for k, v in payload.items():
            print(f"{k}: {v}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run the paper-only Research OS operator evidence sequence")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("run", help="Build closure, verification, attestation, briefing, export, and operator-run manifest")
    r.add_argument("--run-id", default="research-os-operator-run")
    r.add_argument("--operator-id", default="local-operator")
    r.add_argument("--decision", default=ResearchOsOperatorDecision.ACCEPTED_WITH_RESTRICTIONS.value, choices=[d.value for d in ResearchOsOperatorDecision])
    r.add_argument("--rationale", default="Paper-only Research OS operator run evidence acknowledged; not deployment approval.")
    r.add_argument("--constraint", action="append", default=[])
    r.add_argument("--artifact-root", default=None)
    r.add_argument("--repo-root", default=None)
    r.add_argument("--overwrite", action="store_true")
    r.add_argument("--no-export-archive", action="store_true")
    r.add_argument("--json", action="store_true")

    l = sub.add_parser("latest", help="Print latest Research OS operator-run read-plane payload")
    l.add_argument("--artifact-root", default=None)
    l.add_argument("--repo-root", default=None)
    l.add_argument("--json", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    ns = build_parser().parse_args(argv)
    repo_root = Path(ns.repo_root).resolve() if getattr(ns, "repo_root", None) else None
    artifact_root = Path(ns.artifact_root).resolve() if getattr(ns, "artifact_root", None) else None
    try:
        if ns.cmd == "run":
            manifest, path = build_and_write_research_os_operator_run(
                run_id=ns.run_id,
                operator_id=ns.operator_id,
                decision=ns.decision,
                rationale=ns.rationale,
                constraints=list(ns.constraint or []),
                repo_root=repo_root,
                artifact_root=artifact_root,
                overwrite=ns.overwrite,
                include_export_archive=not ns.no_export_archive,
            )
            _emit(
                {
                    "ok": manifest.status.value not in {"BLOCKED", "FAILED", "EMPTY"},
                    "run_id": manifest.run_id,
                    "status": manifest.status.value,
                    "trust_banner": manifest.trust_banner.value,
                    "manifest_path": str(path),
                    "step_count": len(manifest.steps),
                    "warnings": manifest.warnings,
                    "blockers": manifest.blockers,
                    "operator_run_spine_sha256": manifest.digests.get("operator_run_spine_sha256"),
                    "manifest_sha256": manifest.manifest_sha256,
                    "no_live_trading": manifest.no_live_trading,
                    "no_broker_orders": manifest.no_broker_orders,
                    "no_order_controls": manifest.no_order_controls,
                    "deployment_approval_unchanged": manifest.deployment_approval_unchanged,
                },
                as_json=ns.json,
            )
            return 0 if manifest.status.value not in {"BLOCKED", "FAILED", "EMPTY"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_operator_run_latest_payload(repo_root=repo_root, artifact_root=artifact_root), as_json=ns.json)
            return 0
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
