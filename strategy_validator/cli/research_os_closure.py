"""Research OS closure manifest CLI (digest-linked evidence; no trading authority)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    build_ui_research_os_closure_latest_payload,
    load_latest_research_os_closure,
    write_research_os_closure_manifest,
)


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    sys.stdout.write(json.dumps(payload, indent=2 if as_json else None, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build and write a Research OS closure manifest")
    p_build.add_argument("--closure-id", default="research-os-closure")
    p_build.add_argument("--artifact-root", default="")
    p_build.add_argument("--overwrite", action="store_true")
    p_build.add_argument("--json", action="store_true")

    p_latest = sub.add_parser("latest", help="Show latest closure read-plane payload")
    p_latest.add_argument("--json", action="store_true")

    p_verify = sub.add_parser("verify", help="Verify latest closure manifest digest field")
    p_verify.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "build":
            artifact_root = Path(ns.artifact_root) if ns.artifact_root else None
            manifest = build_research_os_closure_manifest(closure_id=ns.closure_id, artifact_root=artifact_root)
            path = write_research_os_closure_manifest(manifest, artifact_root=artifact_root, overwrite=ns.overwrite)
            _emit(
                {
                    "ok": True,
                    "manifest_path": str(path),
                    "status": manifest.status.value,
                    "trust_banner": manifest.trust_banner.value,
                    "present_artifact_count": manifest.present_artifact_count,
                    "warnings": manifest.warnings,
                    "blockers": manifest.blockers,
                    "manifest_sha256": manifest.manifest_sha256,
                    "no_live_trading": True,
                    "no_broker_orders": True,
                },
                as_json=ns.json,
            )
            return 0 if manifest.status.value != "BLOCKED" else 0
        if ns.cmd == "latest":
            _emit(build_ui_research_os_closure_latest_payload(), as_json=ns.json)
            return 0
        if ns.cmd == "verify":
            manifest = load_latest_research_os_closure()
            if manifest is None:
                _emit({"ok": False, "error": "NO_RESEARCH_OS_CLOSURE_MANIFEST"}, as_json=ns.json)
                return 1
            _emit(
                {
                    "ok": bool(manifest.manifest_sha256),
                    "status": manifest.status.value,
                    "trust_banner": manifest.trust_banner.value,
                    "manifest_sha256": manifest.manifest_sha256,
                    "artifact_count": manifest.artifact_count,
                    "present_artifact_count": manifest.present_artifact_count,
                    "no_live_trading": manifest.no_live_trading,
                    "no_broker_orders": manifest.no_broker_orders,
                },
                as_json=ns.json,
            )
            return 0 if manifest.manifest_sha256 else 1
    except Exception as e:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
