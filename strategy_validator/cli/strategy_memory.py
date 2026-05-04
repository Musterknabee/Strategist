"""CLI for Strategy Memory / Candidate Graveyard artifacts (research only)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.application.strategy_memory_ops import (
    build_strategy_memory_index,
    build_ui_strategy_memory_latest_payload,
    ingest_batch_run,
    ingest_paper_tracking,
    load_graveyard_entries,
)


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_batch = sub.add_parser("ingest-batch", help="Ingest batch_summary.json into strategy memory")
    p_batch.add_argument("--batch-run", required=True, help="Batch run directory containing batch_summary.json")
    p_batch.add_argument("--json", action="store_true")

    p_paper = sub.add_parser("ingest-paper", help="Ingest a paper tracking manifest/scorecard/lifecycle into memory")
    p_paper.add_argument("--tracking-id", required=True)
    p_paper.add_argument("--json", action="store_true")

    p_idx = sub.add_parser("build-index", help="Build memory_index.json")
    p_idx.add_argument("--json", action="store_true")

    p_gy = sub.add_parser("list-graveyard", help="List recent graveyard entries")
    p_gy.add_argument("--json", action="store_true")

    p_ui = sub.add_parser("latest", help="Show read-plane latest payload")
    p_ui.add_argument("--json", action="store_true")

    ns = parser.parse_args(argv)

    try:
        if ns.cmd == "ingest-batch":
            records = ingest_batch_run(Path(ns.batch_run))
            _emit(
                {
                    "ok": True,
                    "ingested_count": len(records),
                    "strategy_ids": [r.strategy_id for r in records],
                    "statuses": {r.strategy_id: r.status.value for r in records},
                    "no_live_trading": True,
                },
                as_json=ns.json,
            )
            return 0
        if ns.cmd == "ingest-paper":
            record = ingest_paper_tracking(ns.tracking_id)
            _emit(
                {
                    "ok": True,
                    "tracking_id": ns.tracking_id,
                    "strategy_id": record.strategy_id,
                    "status": record.status.value,
                    "record_sha256": record.record_sha256,
                    "no_live_trading": True,
                },
                as_json=ns.json,
            )
            return 0
        if ns.cmd == "build-index":
            index = build_strategy_memory_index()
            _emit({"ok": True, "index": index.model_dump(mode="json")}, as_json=ns.json)
            return 0
        if ns.cmd == "list-graveyard":
            entries = load_graveyard_entries()
            _emit(
                {
                    "ok": True,
                    "schema_version": "strategy_memory_graveyard_list/v1",
                    "entries": [e.model_dump(mode="json") for e in entries],
                },
                as_json=ns.json,
            )
            return 0
        if ns.cmd == "latest":
            _emit(build_ui_strategy_memory_latest_payload(), as_json=ns.json)
            return 0
    except FileNotFoundError as e:
        _emit({"ok": False, "error": str(e)}, as_json=getattr(ns, "json", False))
        return 2
    except Exception as e:  # pragma: no cover - defensive CLI envelope
        _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, as_json=getattr(ns, "json", False))
        return 1

    parser.print_help()
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
