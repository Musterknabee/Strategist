#!/usr/bin/env python3
"""Build the Research OS evidence catalog demo artifact."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build Research OS evidence catalog demo")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--catalog-id", default="research-os-evidence-catalog-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)

    repo = _repo_root()
    artifact_root = Path(ns.artifact_root)
    if not artifact_root.is_absolute():
        artifact_root = (repo / artifact_root).resolve()

    from strategy_validator.application.research_os_evidence_catalog_ops import build_and_write_research_os_evidence_catalog

    catalog, path = build_and_write_research_os_evidence_catalog(
        catalog_id=ns.catalog_id,
        repo_root=repo,
        artifact_root=artifact_root,
        overwrite=ns.overwrite,
    )
    payload = {
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
    }
    if ns.json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for key, value in payload.items():
            print(f"{key}: {value}", flush=True)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":  # pragma: no cover
    code = main()
    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(code)
