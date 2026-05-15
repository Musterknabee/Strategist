"""Research cycle orchestration: batch evidence → Oracle → wiring → operator run (paper-only)."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from strategy_validator.application.research_os_operator_run_ops import build_and_write_research_os_operator_run
from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.application.strategy_batch_loader import load_strategy_batch_spec
from strategy_validator.contracts.research_cycle_scheduler import ResearchCycleSchedulerState
from strategy_validator.research.strategy_batch_runner import run_strategy_batch

_CYCLE_BATCHES = (
    "example_gauntlet_batch.json",
    "example_batch.json",
    "example_mean_reversion_batch.json",
    "example_price_volume_batch.json",
    "example_chart_pattern_batch.json",
    "example_market_structure_batch.json",
    "example_candlestick_volume_batch.json",
    "example_advanced_technical_batch.json",
    "example_local_bars_batch.json",
    "example_provider_snapshot_batch.json",
)


def _resolve_artifact_root(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)


def research_cycle_scheduler_root(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    return (_resolve_artifact_root(repo_root=repo_root, artifact_root=artifact_root) / "research_cycle_scheduler").resolve()


def scheduler_state_path(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    return research_cycle_scheduler_root(artifact_root=artifact_root, repo_root=repo_root) / "latest" / "scheduler_state.json"


def pending_trigger_path(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    return research_cycle_scheduler_root(artifact_root=artifact_root, repo_root=repo_root) / "pending_trigger.json"


def cycle_lock_path(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    return research_cycle_scheduler_root(artifact_root=artifact_root, repo_root=repo_root) / "cycle.lock"


def last_cycle_report_path(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    return research_cycle_scheduler_root(artifact_root=artifact_root, repo_root=repo_root) / "latest" / "last_cycle_report.json"


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        return raw if isinstance(raw, dict) else None
    except (OSError, json.JSONDecodeError):
        return None


def load_scheduler_state(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> ResearchCycleSchedulerState:
    raw = _read_json(scheduler_state_path(artifact_root=artifact_root, repo_root=repo_root))
    if raw is None:
        return ResearchCycleSchedulerState(updated_at_utc=_utc_now())
    return ResearchCycleSchedulerState.model_validate(raw)


def save_scheduler_state(state: ResearchCycleSchedulerState, *, artifact_root: Path | None = None, repo_root: Path | None = None) -> Path:
    path = scheduler_state_path(artifact_root=artifact_root, repo_root=repo_root)
    _write_json(path, state.model_copy(update={"updated_at_utc": _utc_now()}).model_dump(mode="json"))
    return path


def acquire_cycle_lock(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> bool:
    lock = cycle_lock_path(artifact_root=artifact_root, repo_root=repo_root)
    lock.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, f"{os.getpid()} {_utc_now().isoformat()}\n".encode())
        os.close(fd)
        return True
    except FileExistsError:
        return False


def release_cycle_lock(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> None:
    lock = cycle_lock_path(artifact_root=artifact_root, repo_root=repo_root)
    try:
        lock.unlink(missing_ok=True)
    except OSError:
        pass


def request_research_cycle_trigger(
    *,
    operator_id: str,
    mode: Literal["light", "heavy"] = "light",
    idempotency_key: str | None = None,
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Queue a one-shot cycle for the host daemon (API-safe; no subprocess in-container)."""
    when = _utc_now()
    payload = {
        "schema_version": "research_cycle_trigger/v1",
        "requested_at_utc": when.isoformat(),
        "operator_id": operator_id,
        "mode": mode,
        "idempotency_key": idempotency_key,
    }
    path = pending_trigger_path(artifact_root=artifact_root, repo_root=repo_root)
    _write_json(path, payload)
    state = load_scheduler_state(artifact_root=artifact_root, repo_root=repo_root)
    state = state.model_copy(update={"pending_trigger_count": state.pending_trigger_count + 1})
    save_scheduler_state(state, artifact_root=artifact_root, repo_root=repo_root)
    return {
        "schema_version": "ui_research_cycle_trigger_receipt/v1",
        "generated_at_utc": when.isoformat(),
        "accepted": True,
        "queued": True,
        "mode": mode,
        "operator_id": operator_id,
        "trigger_path": str(path),
        "operator_message": (
            "Research cycle queued for the host scheduler daemon. "
            "Ensure scripts/research_cycle_daemon.py is running 24/7 on the artifact host."
        ),
    }


def consume_pending_trigger(*, artifact_root: Path | None = None, repo_root: Path | None = None) -> dict[str, Any] | None:
    path = pending_trigger_path(artifact_root=artifact_root, repo_root=repo_root)
    raw = _read_json(path)
    if raw is None:
        return None
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass
    state = load_scheduler_state(artifact_root=artifact_root, repo_root=repo_root)
    pending = max(0, state.pending_trigger_count - 1)
    save_scheduler_state(state.model_copy(update={"pending_trigger_count": pending}), artifact_root=artifact_root, repo_root=repo_root)
    return raw


def _batch_spec_for_iteration(iteration: int, repo_root: Path) -> Path:
    name = _CYCLE_BATCHES[iteration % len(_CYCLE_BATCHES)]
    return (repo_root / "configs" / "strategy_batches" / name).resolve()


def _run_runtime_full_cycle(*, repo_root: Path, artifact_root: Path, run_id: str) -> dict[str, Any]:
    batch_spec = repo_root / "configs" / "strategy_batches" / "example_gauntlet_batch.json"
    cmd = [
        sys.executable,
        "-m",
        "strategy_validator.cli.research_os_runtime_demo",
        "--artifact-root",
        str(artifact_root),
        "--run-id",
        run_id,
        "--batch-spec",
        str(batch_spec),
        "--full-research-os-cycle",
        "--allow-synthetic-demo",
        "--overwrite",
        "--skip-benchmark",
        "--json",
    ]
    env = os.environ.copy()
    env["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(artifact_root)
    env["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(artifact_root / "strategy_runs")
    proc = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True)
    return {"ok": proc.returncode == 0, "exit_code": proc.returncode, "stderr_tail": (proc.stderr or "")[-500:]}


def _run_oracle_cycle(*, repo_root: Path, artifact_root: Path, run_next_batch: bool) -> dict[str, Any]:
    script = repo_root / "scripts" / "run_oracle_research_cycle.py"
    cmd = [sys.executable, str(script), "--artifact-root", str(artifact_root), "--json"]
    if run_next_batch:
        cmd.append("--run-next-batch")
    env = os.environ.copy()
    env["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(artifact_root)
    env["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(artifact_root / "strategy_runs")
    proc = subprocess.run(cmd, cwd=repo_root, env=env, capture_output=True, text=True)
    out: dict[str, Any] = {"ok": proc.returncode == 0, "exit_code": proc.returncode}
    if proc.stdout.strip():
        try:
            out["manifest"] = json.loads(proc.stdout)
        except json.JSONDecodeError:
            out["stdout_tail"] = proc.stdout[-500:]
    if proc.stderr:
        out["stderr_tail"] = proc.stderr[-500:]
    return out


def run_research_cycle(
    *,
    mode: Literal["light", "heavy"] = "light",
    artifact_root: Path | None = None,
    repo_root: Path | None = None,
    run_id: str | None = None,
    iteration: int = 0,
    run_next_batch: bool = True,
    allow_network: bool = False,
    overwrite: bool = True,
) -> dict[str, Any]:
    """One closed-loop research iteration (paper-only)."""
    repo = (repo_root or Path.cwd()).resolve()
    art = _resolve_artifact_root(repo_root=repo, artifact_root=artifact_root)
    os.environ["STRATEGY_VALIDATOR_ARTIFACT_ROOT"] = str(art)
    os.environ["STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT"] = str(art / "strategy_runs")

    rid = run_id or f"research-cycle-{mode}-{_utc_now().strftime('%Y%m%dT%H%M%SZ')}"
    batch_path = _batch_spec_for_iteration(iteration, repo)
    report: dict[str, Any] = {
        "schema_version": "research_cycle_report/v1",
        "run_id": rid,
        "mode": mode,
        "started_at_utc": _utc_now().isoformat(),
        "artifact_root": str(art),
        "batch_spec": str(batch_path),
        "steps": {},
        "ok": True,
    }

    try:
        spec = load_strategy_batch_spec(batch_path)
        spec = spec.model_copy(update={"output_root": str(art / "strategy_runs")})
        summary = run_strategy_batch(
            spec,
            allow_synthetic=True,
            fail_fast=False,
            run_id=f"{rid}-batch",
            overwrite=overwrite,
        )
        report["steps"]["batch"] = {
            "ok": True,
            "batch_id": summary.batch_id,
            "run_id": summary.run_id,
            "passed_count": summary.passed_count,
            "strategy_count": summary.strategy_count,
        }
    except Exception as exc:
        report["steps"]["batch"] = {"ok": False, "error": str(exc)}
        report["ok"] = False

    if mode == "heavy":
        report["steps"]["runtime_full_cycle"] = _run_runtime_full_cycle(
            repo_root=repo, artifact_root=art, run_id=f"{rid}-runtime"
        )
        if not report["steps"]["runtime_full_cycle"].get("ok"):
            report["ok"] = False

    if allow_network:
        news_script = repo / "scripts" / "retrieve_provider_samples.py"
        if news_script.is_file():
            samples = art / "provider_samples"
            samples.mkdir(parents=True, exist_ok=True)
            proc = subprocess.run(
                [
                    sys.executable,
                    str(news_script),
                    "--providers",
                    "newsapi",
                    "--output-dir",
                    str(samples),
                    "--manifest-json",
                ],
                cwd=repo,
                capture_output=True,
                text=True,
            )
            report["steps"]["news_fetch"] = {"ok": proc.returncode == 0, "exit_code": proc.returncode}

    report["steps"]["oracle"] = _run_oracle_cycle(repo_root=repo, artifact_root=art, run_next_batch=run_next_batch)
    if not report["steps"]["oracle"].get("ok"):
        report["ok"] = False

    try:
        from strategy_validator.application.operator_evidence_wiring import wire_all_operator_evidence_modules

        report["steps"]["wiring"] = wire_all_operator_evidence_modules(
            artifact_root=art,
            repo_root=repo,
            run_id=rid,
            overwrite=overwrite,
        )
        if not report["steps"]["wiring"].get("ok", True):
            report["ok"] = False
    except Exception as exc:
        report["steps"]["wiring"] = {"ok": False, "error": str(exc)}
        report["ok"] = False

    try:
        manifest, path = build_and_write_research_os_operator_run(
            artifact_root=art,
            repo_root=repo,
            run_id=rid,
            overwrite=overwrite,
        )
        report["steps"]["operator_run"] = {
            "ok": manifest.status.value in {"COMPLETE", "RESTRICTED"},
            "path": str(path),
            "status": manifest.status.value,
        }
        if not report["steps"]["operator_run"]["ok"]:
            report["ok"] = False
    except Exception as exc:
        report["steps"]["operator_run"] = {"ok": False, "error": str(exc)}
        report["ok"] = False

    report["finished_at_utc"] = _utc_now().isoformat()
    _write_json(last_cycle_report_path(artifact_root=art, repo_root=repo), report)
    return report


def build_ui_research_cycle_status_payload(*, repo_root: Path | None = None, artifact_root: Path | None = None) -> dict[str, Any]:
    art = _resolve_artifact_root(repo_root=repo_root, artifact_root=artifact_root)
    state = load_scheduler_state(artifact_root=art, repo_root=repo_root)
    last = _read_json(last_cycle_report_path(artifact_root=art, repo_root=repo_root))
    lock = cycle_lock_path(artifact_root=art, repo_root=repo_root)
    pending = pending_trigger_path(artifact_root=art, repo_root=repo_root)
    oracle_manifest = _read_json(art / "oracle_cycle" / "latest" / "oracle_research_cycle_manifest.json")
    degraded: list[str] = []
    if state.daemon_pid is None:
        degraded.append("DAEMON_NOT_REGISTERED")
    if lock.is_file():
        degraded.append("CYCLE_LOCK_HELD")
    if pending.is_file():
        degraded.append("PENDING_TRIGGER_QUEUED")
    if last is None:
        degraded.append("NO_CYCLE_HISTORY")
    return {
        "schema_version": "ui_research_cycle_status/v1",
        "generated_at_utc": _utc_now().isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "artifact_root": str(art),
        "scheduler": state.model_dump(mode="json"),
        "last_cycle": last,
        "lock_held": lock.is_file(),
        "pending_trigger": pending.is_file(),
        "oracle_fusion_posture": (oracle_manifest or {}).get("fusion_posture"),
        "degraded": degraded,
    }


__all__ = [
    "acquire_cycle_lock",
    "build_ui_research_cycle_status_payload",
    "consume_pending_trigger",
    "load_scheduler_state",
    "release_cycle_lock",
    "request_research_cycle_trigger",
    "run_research_cycle",
    "save_scheduler_state",
]
