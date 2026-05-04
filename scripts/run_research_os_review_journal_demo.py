#!/usr/bin/env python3
"""Build a Research OS review journal demo artifact."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from strategy_validator.application.research_os_review_journal_ops import build_and_write_research_os_review_journal


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Research OS review journal demo.")
    parser.add_argument("--artifact-root", default="artifacts")
    parser.add_argument("--journal-id", default="review-journal-demo")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    journal, path = build_and_write_research_os_review_journal(
        journal_id=args.journal_id,
        artifact_root=Path(args.artifact_root),
        overwrite=bool(args.overwrite),
    )
    payload = journal.model_dump(mode="json")
    payload.update(
        {
            "ok": journal.status.value in {"READY", "RESTRICTED"},
            "artifact_path": str(path),
            "no_live_trading": journal.no_live_trading,
            "no_broker_orders": journal.no_broker_orders,
            "no_order_controls": journal.no_order_controls,
            "deployment_approved": journal.deployment_approved,
        }
    )
    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str), flush=True)
    else:
        print(f"Research OS review journal: {journal.status.value} entries={journal.entry_count} path={path}", flush=True)
    return 0 if payload["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
