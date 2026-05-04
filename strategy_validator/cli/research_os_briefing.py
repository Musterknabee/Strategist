"""Research OS briefing pack CLI.

Evidence/read-plane only: no live trading, no broker orders, no deployment approval.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.research_os_briefing_ops import (
    build_research_os_briefing_pack,
    build_ui_research_os_briefing_latest_payload,
    write_research_os_briefing_pack,
)


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    sys.stdout.write(json.dumps(payload, indent=2 if as_json else None, sort_keys=True) + "\n")


def _artifact_root(raw: str) -> Path | None:
    return Path(raw) if raw else None


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_build = sub.add_parser("build", help="Build latest Research OS operator briefing pack")
    p_build.add_argument("--briefing-id", default="daily-research-briefing")
    p_build.add_argument("--artifact-root", default="")
    p_build.add_argument("--overwrite", action="store_true")
    p_build.add_argument("--json", action="store_true")

    p_latest = sub.add_parser("latest", help="Show latest Research OS briefing read-plane payload")
    p_latest.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)
    try:
        if ns.cmd == "build":
            artifact_root = _artifact_root(ns.artifact_root)
            pack = build_research_os_briefing_pack(briefing_id=ns.briefing_id, artifact_root=artifact_root)
            path = write_research_os_briefing_pack(pack, artifact_root=artifact_root, overwrite=ns.overwrite)
            _emit(
                {
                    "ok": pack.status.value not in {"BLOCKED", "EMPTY"},
                    "status": pack.status.value,
                    "trust_banner": pack.trust_banner.value,
                    "briefing_id": pack.briefing_id,
                    "artifact_path": str(path),
                    "section_count": len(pack.sections),
                    "action_item_count": len(pack.action_items),
                    "warnings": pack.warnings,
                    "blockers": pack.blockers,
                    "briefing_sha256": pack.briefing_sha256,
                    "no_live_trading": True,
                    "no_broker_orders": True,
                },
                as_json=ns.json,
            )
            return 0 if pack.status.value not in {"BLOCKED", "EMPTY"} else 1
        if ns.cmd == "latest":
            _emit(build_ui_research_os_briefing_latest_payload(), as_json=ns.json)
            return 0
    except Exception as exc:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(exc).__name__}: {exc}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
