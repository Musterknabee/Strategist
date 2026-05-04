#!/usr/bin/env python
"""Build a demo Research OS single-tenant handoff pack."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_handoff_ops import build_and_write_research_os_handoff_pack


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Research OS handoff demo.")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--handoff-id", default="handoff-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    pack, path = build_and_write_research_os_handoff_pack(
        artifact_root=Path(args.artifact_root),
        handoff_id=args.handoff_id,
        overwrite=bool(args.overwrite),
    )
    payload = {
        "ok": pack.status.value not in {"BLOCKED", "EMPTY"},
        "status": pack.status.value,
        "decision": pack.decision.value,
        "handoff_ready": pack.handoff_ready,
        "restricted_handoff": pack.restricted_handoff,
        "trust_banner": pack.trust_banner.value,
        "blocker_count": len(pack.blockers),
        "warning_count": len(pack.warnings),
        "artifact_path": str(path),
        "manifest_sha256": pack.manifest_sha256,
        "no_live_trading": pack.no_live_trading,
        "no_broker_orders": pack.no_broker_orders,
        "no_order_controls": pack.no_order_controls,
    }
    print(json.dumps(payload if args.json else payload, indent=2, sort_keys=True), flush=True)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
