#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_export_ops import (
    build_research_os_export_manifest,
    research_os_export_latest_manifest_path,
    verify_research_os_export,
)


def main() -> int:
    p = argparse.ArgumentParser(description="Build a no-network Research OS export demo bundle")
    p.add_argument("--artifact-root", default="artifacts")
    p.add_argument("--export-id", default="research-os-export-demo")
    p.add_argument("--overwrite", action="store_true")
    p.add_argument("--no-archive", action="store_true")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args()
    artifact_root = Path(ns.artifact_root).resolve()
    manifest = build_research_os_export_manifest(
        export_id=ns.export_id,
        artifact_root=artifact_root,
        overwrite=ns.overwrite,
        include_archive=not ns.no_archive,
    )
    verification = verify_research_os_export(
        manifest_path=research_os_export_latest_manifest_path(artifact_root=artifact_root),
        artifact_root=artifact_root,
        write_latest=True,
    )
    payload = {
        "ok": manifest.status.value not in {"BLOCKED", "EMPTY"},
        "export_id": manifest.export_id,
        "status": manifest.status.value,
        "trust_banner": manifest.trust_banner.value,
        "bundle_directory": manifest.bundle_directory,
        "archive_path": manifest.archive_path,
        "file_count": len(manifest.files),
        "present_file_count": len([f for f in manifest.files if f.present and f.readable]),
        "verification_status": verification.status.value,
        "warnings": manifest.warnings,
        "blockers": manifest.blockers,
        "manifest_sha256": manifest.manifest_sha256,
        "no_live_trading": True,
        "no_broker_orders": True,
    }
    if ns.json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for k, v in payload.items():
            print(f"{k}: {v}", flush=True)
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
