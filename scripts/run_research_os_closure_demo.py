#!/usr/bin/env python3
"""Build a Research OS closure manifest for the current artifact root."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.research_os_closure_ops import (
    build_research_os_closure_manifest,
    write_research_os_closure_manifest,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--closure-id", default="research-os-closure-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)
    artifact_root = Path(ns.artifact_root).expanduser().resolve()
    manifest = build_research_os_closure_manifest(closure_id=ns.closure_id, artifact_root=artifact_root)
    path = write_research_os_closure_manifest(manifest, artifact_root=artifact_root, overwrite=ns.overwrite)
    payload = {
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
    }
    sys.stdout.write(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True) + "\n")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
