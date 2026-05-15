#!/usr/bin/env python3
"""24/7 research cycle scheduler (host-side; paper-only).

Polls artifact_root/research_cycle_scheduler/pending_trigger.json and runs
light/heavy cycles on an interval. Use install/start scripts on Windows.
"""
from __future__ import annotations

import argparse
import os
import signal
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_STOP = False


def _handle_stop(*_args: object) -> None:
    global _STOP
    _STOP = True


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
    p.add_argument("--interval-seconds", type=int, default=3600, help="Sleep between automatic cycles (default 1h)")
    p.add_argument("--heavy-every", type=int, default=12, help="Run heavy cycle every N iterations")
    p.add_argument("--allow-network", action="store_true", help="Fetch NewsAPI during cycles when configured")
    p.add_argument("--once", action="store_true", help="Run a single cycle then exit")
    p.add_argument("--json", action="store_true")
    ns = p.parse_args(argv)

    art = _artifact_root(ns.artifact_root)
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    os.environ["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")

    from strategy_validator.application.research_cycle_ops import (
        acquire_cycle_lock,
        consume_pending_trigger,
        load_scheduler_state,
        release_cycle_lock,
        run_research_cycle,
        save_scheduler_state,
    )
    from strategy_validator.contracts.research_cycle_scheduler import ResearchCycleSchedulerState

    signal.signal(signal.SIGINT, _handle_stop)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, _handle_stop)

    iteration = load_scheduler_state(artifact_root=art, repo_root=_REPO).iteration
    explicit_trigger: dict | None = None
    print(f"research_cycle_daemon pid={os.getpid()} artifact_root={art}", flush=True)
    print(f"  interval={ns.interval_seconds}s heavy_every={ns.heavy_every}", flush=True)

    def register_daemon() -> None:
        from datetime import datetime, timezone

        state = load_scheduler_state(artifact_root=art, repo_root=_REPO)
        state = state.model_copy(
            update={
                "daemon_pid": os.getpid(),
                "daemon_started_at_utc": datetime.now(timezone.utc),
                "interval_seconds": ns.interval_seconds,
                "heavy_every": max(1, ns.heavy_every),
                "allow_network": ns.allow_network,
            }
        )
        save_scheduler_state(state, artifact_root=art, repo_root=_REPO)

    register_daemon()

    while not _STOP:
        trigger = explicit_trigger
        if trigger is None:
            trigger = consume_pending_trigger(artifact_root=art, repo_root=_REPO)
        explicit_trigger = None
        mode = str((trigger or {}).get("mode") or "light")
        if trigger is None:
            mode = "heavy" if ns.heavy_every > 0 and iteration > 0 and iteration % ns.heavy_every == 0 else "light"

        if not acquire_cycle_lock(artifact_root=art, repo_root=_REPO):
            print("cycle lock held; skipping", flush=True)
            if ns.once:
                return 0
            time.sleep(min(60, ns.interval_seconds))
            continue

        rid = f"daemon-{mode}-iter{iteration}"
        from datetime import datetime, timezone

        state = load_scheduler_state(artifact_root=art, repo_root=_REPO)
        state = state.model_copy(
            update={
                "iteration": iteration,
                "last_cycle_started_at_utc": datetime.now(timezone.utc),
                "last_cycle_mode": mode if mode in ("light", "heavy") else "light",
                "daemon_pid": os.getpid(),
            }
        )
        save_scheduler_state(state, artifact_root=art, repo_root=_REPO)

        try:
            report = run_research_cycle(
                mode=mode if mode in ("light", "heavy") else "light",
                artifact_root=art,
                repo_root=_REPO,
                run_id=rid,
                iteration=iteration,
                allow_network=ns.allow_network,
            )
            ok = bool(report.get("ok"))
            if ns.json:
                import json

                print(json.dumps(report, indent=2, sort_keys=True), flush=True)
            else:
                print(f"cycle finished ok={ok} mode={mode} iter={iteration}", flush=True)
        except Exception as exc:
            ok = False
            print(f"cycle error: {exc}", flush=True)
        finally:
            release_cycle_lock(artifact_root=art, repo_root=_REPO)

        iteration += 1
        state = load_scheduler_state(artifact_root=art, repo_root=_REPO)
        state = state.model_copy(
            update={
                "iteration": iteration,
                "last_cycle_finished_at_utc": datetime.now(timezone.utc),
                "last_cycle_ok": ok,
                "last_cycle_run_id": rid,
                "last_cycle_error": None if ok else "cycle_failed",
            }
        )
        save_scheduler_state(state, artifact_root=art, repo_root=_REPO)

        if ns.once:
            return 0 if ok else 1

        if trigger is not None:
            continue

        slept = 0
        while slept < ns.interval_seconds and not _STOP:
            time.sleep(min(30, ns.interval_seconds - slept))
            slept += min(30, ns.interval_seconds - slept)
            mid_trigger = consume_pending_trigger(artifact_root=art, repo_root=_REPO)
            if mid_trigger is not None:
                explicit_trigger = mid_trigger
                break

        if explicit_trigger is not None:
            continue

    state = load_scheduler_state(artifact_root=art, repo_root=_REPO)
    save_scheduler_state(state.model_copy(update={"daemon_pid": None}), artifact_root=art, repo_root=_REPO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
