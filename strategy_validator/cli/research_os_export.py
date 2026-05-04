from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_export_ops import (
    build_research_os_export_manifest,
    build_ui_research_os_export_latest_payload,
    research_os_export_latest_manifest_path,
    verify_research_os_export,
)


def _emit(payload: dict[str, Any], *, as_json: bool) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True), flush=True)
    else:
        for k, v in payload.items():
            print(f"{k}: {v}", flush=True)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Build and verify Research OS portable evidence export bundles")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build", help="Build a portable Research OS evidence export bundle")
    b.add_argument("--export-id", default="research-os-export")
    b.add_argument("--artifact-root", default=None)
    b.add_argument("--repo-root", default=None)
    b.add_argument("--overwrite", action="store_true")
    b.add_argument("--no-archive", action="store_true")
    b.add_argument("--json", action="store_true")

    v = sub.add_parser("verify", help="Verify the latest or selected Research OS export bundle")
    v.add_argument("--manifest", default=None)
    v.add_argument("--artifact-root", default=None)
    v.add_argument("--repo-root", default=None)
    v.add_argument("--no-write", action="store_true")
    v.add_argument("--json", action="store_true")

    l = sub.add_parser("latest", help="Print latest Research OS export read-plane payload")
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
            manifest = build_research_os_export_manifest(
                export_id=ns.export_id,
                repo_root=repo_root,
                artifact_root=artifact_root,
                overwrite=ns.overwrite,
                include_archive=not ns.no_archive,
            )
            result = verify_research_os_export(
                manifest_path=research_os_export_latest_manifest_path(repo_root, artifact_root),
                repo_root=repo_root,
                artifact_root=artifact_root,
                write_latest=True,
            )
            _emit(
                {
                    "ok": manifest.status.value not in {"BLOCKED", "EMPTY"},
                    "export_id": manifest.export_id,
                    "status": manifest.status.value,
                    "trust_banner": manifest.trust_banner.value,
                    "bundle_directory": manifest.bundle_directory,
                    "archive_path": manifest.archive_path,
                    "archive_sha256": manifest.archive_sha256,
                    "file_count": len(manifest.files),
                    "present_file_count": len([f for f in manifest.files if f.present and f.readable]),
                    "warnings": manifest.warnings,
                    "blockers": manifest.blockers,
                    "export_spine_sha256": manifest.export_spine_sha256,
                    "manifest_sha256": manifest.manifest_sha256,
                    "verification_status": result.status.value,
                    "no_live_trading": True,
                    "no_broker_orders": True,
                },
                as_json=ns.json,
            )
            return 0 if manifest.status.value not in {"BLOCKED", "EMPTY"} else 1
        if ns.cmd == "verify":
            result = verify_research_os_export(
                manifest_path=Path(ns.manifest).resolve() if ns.manifest else None,
                repo_root=repo_root,
                artifact_root=artifact_root,
                write_latest=not ns.no_write,
            )
            _emit(result.model_dump(mode="json"), as_json=ns.json)
            return 0 if result.status.value not in {"BLOCKED", "EMPTY"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_export_latest_payload(repo_root=repo_root, artifact_root=artifact_root), as_json=ns.json)
            return 0
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
