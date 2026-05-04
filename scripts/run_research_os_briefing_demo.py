#!/usr/bin/env python3
"""Build a Research OS briefing pack from existing local evidence artifacts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Support direct execution from a source checkout.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from strategy_validator.application.research_os_briefing_ops import (  # noqa: E402
    build_research_os_briefing_pack,
    write_research_os_briefing_pack,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--briefing-id", default="research-os-briefing-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    ns = parser.parse_args(argv)

    artifact_root = Path(ns.artifact_root)
    pack = build_research_os_briefing_pack(briefing_id=ns.briefing_id, artifact_root=artifact_root)
    path = write_research_os_briefing_pack(pack, artifact_root=artifact_root, overwrite=ns.overwrite)
    payload = {
        "ok": pack.status.value not in {"BLOCKED", "EMPTY"},
        "status": pack.status.value,
        "trust_banner": pack.trust_banner.value,
        "briefing_id": pack.briefing_id,
        "artifact_path": str(path),
        "section_count": len(pack.sections),
        "action_item_count": len(pack.action_items),
        "briefing_sha256": pack.briefing_sha256,
        "no_live_trading": True,
        "no_broker_orders": True,
    }
    sys.stdout.write(json.dumps(payload, indent=2 if ns.json else None, sort_keys=True) + "\n")
    return 0 if payload["ok"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
