#!/usr/bin/env python3
"""Run one research cycle iteration (batch → Oracle → wiring → operator run)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


def _artifact_root(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).resolve()
    for candidate in (
        os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", ""),
        r"C:\var\lib\strategy-validator\artifacts",
        str(_REPO / "artifacts"),
    ):
        if candidate:
            p = Path(candidate).resolve()
            p.mkdir(parents=True, exist_ok=True)
            return p
    return (_REPO / "artifacts").resolve()


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--artifact-root", default=None)
    p.add_argument("--mode", choices=("light", "heavy"), default="light")
    p.add_argument("--run-id", default=None)
    p.add_argument("--iteration", type=int, default=0)
    p.add_argument("--no-run-next-batch", action="store_true")
    p.add_argument("--allow-network", action="store_true")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    art = _artifact_root(ns.artifact_root)
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)

    from strategy_validator.application.research_cycle_ops import run_research_cycle

    report = run_research_cycle(
        mode=ns.mode,
        artifact_root=art,
        repo_root=_REPO,
        run_id=ns.run_id,
        iteration=ns.iteration,
        run_next_batch=not ns.no_run_next_batch,
        allow_network=ns.allow_network,
    )
    if ns.json:
        print(json.dumps(report, indent=2, sort_keys=True), flush=True)
    else:
        print(f"research cycle ok={report.get('ok')} mode={report.get('mode')} run_id={report.get('run_id')}", flush=True)
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
