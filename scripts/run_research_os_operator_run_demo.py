#!/usr/bin/env python3
"""Run the paper-only Research OS operator sequence demo."""
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
    parser = argparse.ArgumentParser(description="Run Research OS operator-run demo")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--run-id", default="research-os-operator-run-demo")
    parser.add_argument("--operator-id", default="local-operator")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--no-export-archive", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)

    repo = _repo_root()
    artifact_root = Path(ns.artifact_root)
    if not artifact_root.is_absolute():
        artifact_root = (repo / artifact_root).resolve()

    from strategy_validator.application.research_os_operator_run_ops import build_and_write_research_os_operator_run

    manifest, path = build_and_write_research_os_operator_run(
        run_id=ns.run_id,
        operator_id=ns.operator_id,
        repo_root=repo,
        artifact_root=artifact_root,
        overwrite=ns.overwrite,
        include_export_archive=not ns.no_export_archive,
    )
    payload = {
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
