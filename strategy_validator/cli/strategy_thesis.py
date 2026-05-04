"""CLI for Strategy Thesis / Falsification Manifest evaluation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from strategy_validator.research.strategy_thesis_eval import (
    build_ui_strategy_thesis_latest_payload,
    evaluate_from_paths,
    list_thesis_evaluations,
)
from strategy_validator.research.strategy_thesis_generator import generate_from_paths


def _emit(payload: dict[str, object], *, as_json: bool) -> None:
    if as_json:
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    else:
        sys.stdout.write(json.dumps(payload, sort_keys=True) + "\n")


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    ev = sub.add_parser("evaluate", help="Evaluate a thesis against a batch_summary.json or run directory")
    ev.add_argument("--strategy-run", required=True)
    ev.add_argument("--thesis", required=True)
    ev.add_argument("--output-root", default="")
    ev.add_argument("--json", action="store_true")

    gen = sub.add_parser("generate-from-batch", help="Generate Oracle research theses from a batch_summary.json or run directory")
    gen.add_argument("--strategy-run", required=True)
    gen.add_argument("--output-root", default="")
    gen.add_argument("--no-evaluate", action="store_true", help="Only write thesis.json artifacts; skip immediate thesis evaluation")
    gen.add_argument("--json", action="store_true")

    ls = sub.add_parser("list", help="List thesis evaluations")
    ls.add_argument("--json", action="store_true")

    latest = sub.add_parser("latest", help="Show latest UI payload")
    latest.add_argument("--json", action="store_true")

    ns = p.parse_args(argv)
    try:
        if ns.cmd == "evaluate":
            evaluation = evaluate_from_paths(
                strategy_run=Path(ns.strategy_run),
                thesis_path=Path(ns.thesis),
                output_root=Path(ns.output_root) if ns.output_root else None,
            )
            _emit({"ok": True, "evaluation": evaluation.model_dump(mode="json"), "no_live_trading": True}, as_json=ns.json)
            return 0 if evaluation.support_status.value != "FALSIFIED" else 0
        if ns.cmd == "generate-from-batch":
            generation_report = generate_from_paths(
                strategy_run=Path(ns.strategy_run),
                output_root=Path(ns.output_root) if ns.output_root else None,
                evaluate=not ns.no_evaluate,
            )
            _emit({"ok": True, "generation_report": generation_report.model_dump(mode="json"), "no_live_trading": True}, as_json=ns.json)
            return 0
        if ns.cmd == "list":
            _emit({"ok": True, "evaluations": list_thesis_evaluations()}, as_json=ns.json)
            return 0
        if ns.cmd == "latest":
            _emit(build_ui_strategy_thesis_latest_payload(), as_json=ns.json)
            return 0
    except FileNotFoundError as e:
        _emit({"ok": False, "error": str(e)}, as_json=getattr(ns, "json", False))
        return 2
    except Exception as e:  # pragma: no cover
        _emit({"ok": False, "error": f"{type(e).__name__}: {e}"}, as_json=getattr(ns, "json", False))
        return 1
    return 2


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
