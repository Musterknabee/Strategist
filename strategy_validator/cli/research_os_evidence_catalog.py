from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_evidence_catalog_ops import (
    build_and_write_research_os_evidence_catalog,
    build_ui_research_os_evidence_catalog_latest_payload,
)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for k, v in payload.items():
            print(f"{k}: {v}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build/read the Research OS evidence catalog")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Scan artifact root and write the evidence catalog")
    b.add_argument("--catalog-id", default="research-os-evidence-catalog")
    b.add_argument("--artifact-root", default=None)
    b.add_argument("--repo-root", default=None)
    b.add_argument("--overwrite", action="store_true")
    b.add_argument("--json", action="store_true")

    l = sub.add_parser("latest", help="Print latest catalog read-plane payload")
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
            catalog, path = build_and_write_research_os_evidence_catalog(
                catalog_id=ns.catalog_id,
                repo_root=repo_root,
                artifact_root=artifact_root,
                overwrite=ns.overwrite,
            )
            _emit(
                {
                    "ok": catalog.status.value not in {"BLOCKED", "EMPTY"},
                    "catalog_id": catalog.catalog_id,
                    "status": catalog.status.value,
                    "trust_banner": catalog.trust_banner.value,
                    "manifest_path": str(path),
                    "entry_count": catalog.entry_count,
                    "latest_entry_count": catalog.latest_entry_count,
                    "category_counts": catalog.category_counts,
                    "warnings": catalog.warnings,
                    "blockers": catalog.blockers,
                    "catalog_spine_sha256": catalog.catalog_spine_sha256,
                    "manifest_sha256": catalog.manifest_sha256,
                    "no_live_trading": catalog.no_live_trading,
                    "no_broker_orders": catalog.no_broker_orders,
                    "no_order_controls": catalog.no_order_controls,
                    "deployment_approval_unchanged": catalog.deployment_approval_unchanged,
                },
                as_json=ns.json,
            )
            return 0 if catalog.status.value not in {"BLOCKED", "EMPTY"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_evidence_catalog_latest_payload(repo_root=repo_root, artifact_root=artifact_root), as_json=ns.json)
            return 0
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
