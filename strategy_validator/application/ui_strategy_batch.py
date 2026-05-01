"""Read-plane payloads for strategy batch lab artifacts (no execution)."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary

_SCHEMA = "ui_strategy_batch/v1"


def _default_scan_root(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    art = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if art:
        return (Path(art).expanduser().resolve() / "strategy_runs")
    root = repo_root or Path.cwd()
    return (root / "artifacts" / "strategy_runs").resolve()


def _find_batch_summaries(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(root.rglob("batch_summary.json"), key=lambda p: p.stat().st_mtime, reverse=True)


def _safe_read_summary(path: Path) -> StrategyBatchRunSummary | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return StrategyBatchRunSummary.model_validate(data)
    except (OSError, json.JSONDecodeError, ValueError):
        return None


def discover_latest_batch_summary(*, repo_root: Path | None = None) -> tuple[Path | None, StrategyBatchRunSummary | None]:
    root = _default_scan_root(repo_root)
    for candidate in _find_batch_summaries(root):
        summary = _safe_read_summary(candidate)
        if summary is not None:
            return candidate, summary
    return None, None


def discover_batch_by_run_id(run_id: str, *, repo_root: Path | None = None) -> tuple[Path | None, StrategyBatchRunSummary | None]:
    root = _default_scan_root(repo_root)
    for path in root.rglob("batch_summary.json"):
        if path.parent.name == run_id:
            summary = _safe_read_summary(path)
            if summary is not None and summary.run_id == run_id:
                return path, summary
    return None, None


def _read_portfolio_allocation(run_dir: Path | None) -> dict[str, Any] | None:
    if run_dir is None:
        return None
    p = run_dir / "portfolio_allocation_result.json"
    if not p.is_file():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def build_ui_strategy_batch_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    path, summary = discover_latest_batch_summary(repo_root=repo_root)
    degraded: list[str] = []
    if path is None:
        degraded.append("NO_BATCH_ARTIFACTS")
    run_dir = path.parent if path else None
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_root": str(_default_scan_root(repo_root)),
        "summary_path": str(path) if path else None,
        "degraded": degraded,
        "latest": summary.model_dump(mode="json") if summary else None,
        "portfolio_allocation": _read_portfolio_allocation(run_dir),
    }


def build_ui_strategy_batch_list_payload(*, repo_root: Path | None = None, limit: int = 32) -> dict[str, Any]:
    root = _default_scan_root(repo_root)
    rows: list[dict[str, Any]] = []
    for path in _find_batch_summaries(root)[:limit]:
        s = _safe_read_summary(path)
        if s is None:
            continue
        rows.append(
            {
                "batch_id": s.batch_id,
                "run_id": s.run_id,
                "generated_at_utc": s.generated_at_utc.isoformat(),
                "ok": s.ok,
                "strategy_count": s.strategy_count,
                "paper_only_count": s.paper_only_count,
                "failed_count": s.failed_count,
                "summary_path": str(path),
            }
        )
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scan_root": str(root),
        "batches": rows,
        "degraded": [] if root.is_dir() else ["SCAN_ROOT_MISSING"],
    }


def build_ui_strategy_batch_detail_payload(run_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    path, summary = discover_batch_by_run_id(run_id, repo_root=repo_root)
    degraded: list[str] = []
    if summary is None:
        degraded.append("BATCH_NOT_FOUND")
    run_dir = path.parent if path else None
    return {
        "schema_version": _SCHEMA,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "summary_path": str(path) if path else None,
        "degraded": degraded,
        "batch": summary.model_dump(mode="json") if summary else None,
        "portfolio_allocation": _read_portfolio_allocation(run_dir),
    }


__all__ = [
    "build_ui_strategy_batch_detail_payload",
    "build_ui_strategy_batch_latest_payload",
    "build_ui_strategy_batch_list_payload",
    "discover_batch_by_run_id",
    "discover_latest_batch_summary",
]
