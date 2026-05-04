"""Backtest forensic review projection for the operator UI."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.ui_strategy_batch import _default_scan_root, discover_batch_by_run_id, discover_latest_batch_summary
from strategy_validator.contracts.backtest_forensics import (
    BacktestForensicStrategyRow,
    BacktestForensicsPayload,
    BacktestForensicsSummary,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult

_SCHEMA = "ui_backtest_forensics/v1"


def _upper(v: Any) -> str:
    if v is None:
        return "UNKNOWN"
    if hasattr(v, "value"):
        v = v.value
    return str(v).upper()


def _gate_summary(row: StrategyRunResult) -> dict[str, Any]:
    gate = getattr(row, "gate_summary", None)
    if gate is None:
        return {}
    data = gate.model_dump(mode="json") if hasattr(gate, "model_dump") else dict(gate)
    data.setdefault("promotion_eligible", bool(getattr(gate, "promotion_eligible", False)))
    data.setdefault("promotion_blocked_reasons", list(getattr(gate, "promotion_blocked_reasons", ()) or ()))
    return data


def _promotion_blocked(row: StrategyRunResult, gate: dict[str, Any]) -> list[str]:
    reasons = list(gate.get("promotion_blocked_reasons") or [])
    for b in getattr(row, "blockers", ()) or ():
        if b not in reasons:
            reasons.append(str(b))
    return reasons


def _risk_flags(row: StrategyRunResult, gate: dict[str, Any]) -> list[str]:
    flags: list[str] = []
    data_plane = _upper(getattr(row, "data_plane", None))
    status = _upper(getattr(row, "status", None))
    if data_plane == "SYNTHETIC":
        flags.append("SYNTHETIC_DATA_PAPER_ONLY")
    if status == "PAPER_ONLY":
        flags.append("PAPER_ONLY_STATUS")
    if not bool(gate.get("promotion_eligible", False)):
        flags.append("PROMOTION_BLOCKED")
    if _upper(gate.get("robustness_gate")) in {"NOT_RUN", "UNKNOWN", "BLOCKED"}:
        flags.append("ROBUSTNESS_NOT_PROVEN")
    if _upper(gate.get("cpcv_robustness_gate")) in {"NOT_RUN", "UNKNOWN", "BLOCKED"}:
        flags.append("CPCV_NOT_PROVEN")
    if _upper(gate.get("execution_realism_gate")) in {"NOT_RUN", "UNKNOWN", "BLOCKED"}:
        flags.append("EXECUTION_REALISM_NOT_PROVEN")
    if not getattr(row, "evidence_manifest_path", None):
        flags.append("MISSING_EVIDENCE_MANIFEST")
    return list(dict.fromkeys(flags))


def _posture(row: StrategyRunResult, gate: dict[str, Any], flags: list[str]) -> tuple[str, str]:
    if bool(gate.get("promotion_eligible", False)):
        return "REVIEW_READY", "Promotion review evidence appears present; validator authority still required."
    status = _upper(getattr(row, "status", None))
    if status in {"BLOCKED", "FAILED"}:
        return "BLOCKED", "Resolve blockers before spending promotion-review budget."
    if status == "PAPER_ONLY":
        return "PAPER_ONLY", "Keep in paper/research mode until data, PIT, robustness, and execution realism evidence are complete."
    if any(f.endswith("NOT_PROVEN") or f == "MISSING_EVIDENCE_MANIFEST" for f in flags):
        return "NEEDS_EVIDENCE", "Attach missing forensic evidence before review."
    return "OBSERVE", "Monitor as research evidence only."


def _artifacts(row: StrategyRunResult) -> dict[str, Any]:
    paths = {
        "evidence_manifest": getattr(row, "evidence_manifest_path", None),
        "scorecard": getattr(row, "strategy_scorecard_path", None),
        "robustness": getattr(row, "robustness_artifact_path", None),
        "cpcv": getattr(row, "cpcv_artifact_path", None),
    }
    observed = {
        "evidence_manifest": getattr(row, "evidence_manifest_sha256", None),
        "robustness": getattr(row, "robustness_evidence_sha256", None),
        "cpcv": getattr(row, "cpcv_evidence_sha256", None),
    }
    return {"paths": paths, "observed_sha256": observed}


def _forensic_row(row: StrategyRunResult) -> BacktestForensicStrategyRow:
    gate = _gate_summary(row)
    blocked = _promotion_blocked(row, gate)
    flags = _risk_flags(row, gate)
    posture, recommendation = _posture(row, gate, flags)
    return BacktestForensicStrategyRow(
        strategy_id=row.strategy_id,
        status=_upper(row.status),
        decision=getattr(row, "decision", None),
        review_posture=posture,
        review_recommendation=recommendation,
        promotion_eligible=bool(gate.get("promotion_eligible", False)),
        promotion_blocked_reasons=blocked,
        risk_flags=flags,
        warnings=list(getattr(row, "warnings", ()) or ()),
        blockers=list(getattr(row, "blockers", ()) or ()),
        data_plane=_upper(getattr(row, "data_plane", None)),
        data_status=_upper(getattr(row, "data_status", None)),
        pit_status=_upper(getattr(row, "pit_status", None)),
        pit_snapshot_status=getattr(row, "pit_snapshot_status", None),
        bars_row_count=getattr(row, "bars_row_count", None),
        gate_matrix=gate,
        metrics={
            "total_return": getattr(row, "total_return", None),
            "max_drawdown": getattr(row, "max_drawdown", None),
            "sharpe_like": getattr(row, "sharpe_like", None),
            "analytics_score": getattr(row, "analytics_score", None),
            "analytics_rank": getattr(row, "analytics_rank", None),
        },
        robustness={
            "gate_status": gate.get("robustness_gate"),
            "cpcv_gate_status": gate.get("cpcv_robustness_gate"),
            "pbo_like_score": getattr(row, "pbo_like_score", None),
            "dsr_like_score": getattr(row, "dsr_like_score", None),
        },
        execution_realism={
            "gate_status": gate.get("execution_realism_gate"),
            "model_label": getattr(row, "execution_realism_model_label", None),
            "estimated_slippage_bps": getattr(row, "execution_realism_est_slippage_bps", None),
            "estimated_fee_bps": getattr(row, "execution_realism_est_fee_bps", None),
        },
        artifacts=_artifacts(row),
    )


def _gate_status_counts(rows: list[BacktestForensicStrategyRow]) -> dict[str, dict[str, int]]:
    counts: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        for key, value in row.gate_matrix.items():
            if key in {"promotion_eligible", "promotion_blocked_reasons"}:
                continue
            counts[key][str(value)] += 1
    return {k: dict(v) for k, v in sorted(counts.items())}


def _summary(summary: StrategyBatchRunSummary | None, rows: list[BacktestForensicStrategyRow]) -> BacktestForensicsSummary:
    flag_counter: Counter[str] = Counter()
    for row in rows:
        flag_counter.update(row.risk_flags)
    return BacktestForensicsSummary(
        batch_present=summary is not None,
        strategy_count=len(rows),
        promotion_eligible_count=sum(1 for r in rows if r.promotion_eligible),
        blocked_count=sum(1 for r in rows if r.review_posture == "BLOCKED"),
        paper_only_count=sum(1 for r in rows if r.review_posture == "PAPER_ONLY"),
        failed_count=sum(1 for r in rows if r.status == "FAILED"),
        needs_evidence_count=sum(1 for r in rows if r.review_posture == "NEEDS_EVIDENCE"),
        synthetic_count=sum(1 for r in rows if r.data_plane == "SYNTHETIC"),
        provider_snapshot_count=sum(1 for r in rows if r.data_plane == "PROVIDER_SNAPSHOT"),
        real_local_count=sum(1 for r in rows if r.data_plane == "REAL_LOCAL"),
        risk_flag_counts=dict(sorted(flag_counter.items())),
        gate_status_counts=_gate_status_counts(rows),
    )


def _batch_overview(summary: StrategyBatchRunSummary | None) -> dict[str, Any] | None:
    if summary is None:
        return None
    return {
        "schema_version": summary.schema_version,
        "batch_id": summary.batch_id,
        "run_id": summary.run_id,
        "ok": summary.ok,
        "generated_at_utc": summary.generated_at_utc.isoformat(),
        "output_dir": summary.output_dir,
        "strategy_count": summary.strategy_count,
        "passed_count": summary.passed_count,
        "blocked_count": summary.blocked_count,
        "paper_only_count": summary.paper_only_count,
        "failed_count": summary.failed_count,
        "pending_count": summary.pending_count,
        "top_candidate": summary.top_candidate,
        "promotion_blocked_counts": summary.promotion_blocked_counts,
        "portfolio_correlation_summary": summary.portfolio_correlation_summary,
        "blockers": summary.blockers,
        "warnings": summary.warnings,
    }


def _payload(path: Path | None, summary: StrategyBatchRunSummary | None, *, repo_root: Path | None, route: str) -> dict[str, Any]:
    degraded: list[str] = []
    if path is None or summary is None:
        degraded.append("NO_BATCH_ARTIFACTS" if route.endswith("latest") else "BATCH_NOT_FOUND")
    rows = [_forensic_row(row) for row in (summary.strategies if summary else [])]
    return BacktestForensicsPayload(
        scan_root=str(_default_scan_root(repo_root)),
        summary_path=str(path) if path else None,
        degraded=degraded,
        batch=_batch_overview(summary),
        summary=_summary(summary, rows),
        strategies=rows,
        raw_strategy_batch_route=route,
    ).model_dump(mode="json")


def build_ui_backtest_forensics_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    path, summary = discover_latest_batch_summary(repo_root=repo_root)
    return _payload(path, summary, repo_root=repo_root, route="/ui/strategy-batches/latest")


def build_ui_backtest_forensics_detail_payload(run_id: str, *, repo_root: Path | None = None) -> dict[str, Any]:
    path, summary = discover_batch_by_run_id(run_id, repo_root=repo_root)
    return _payload(path, summary, repo_root=repo_root, route=f"/ui/strategy-batches/{run_id}")


__all__ = ["build_ui_backtest_forensics_detail_payload", "build_ui_backtest_forensics_latest_payload"]
