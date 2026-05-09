"""Backtest forensic review projection for the operator UI."""
from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_research_replay import latest_replay_verification_summary
from strategy_validator.application.ui_strategy_batch import (
    _default_scan_root,
    discover_batch_by_run_id,
    discover_latest_batch_summary,
)
from strategy_validator.contracts.backtest_forensics import (
    BacktestForensicStrategyRow,
    BacktestForensicsPayload,
    BacktestForensicsSummary,
)
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult

_SCHEMA = "ui_backtest_forensics/v1"


def _replay_evidence_status(replay: dict[str, Any]) -> dict[str, Any]:
    status = str(replay.get("status") or "UNKNOWN").upper()
    missing = int(replay.get("missing_artifact_count") or 0)
    mismatch = int(replay.get("digest_mismatch_count") or 0)
    if mismatch > 0 or status == "DEGRADED":
        return {"status": "DEGRADED", "blocked": True}
    if status == "OK" and missing == 0:
        return {"status": "OK", "blocked": False}
    return {"status": "UNKNOWN", "blocked": False}


def _upper(v: Any) -> str:
    if v is None:
        return "UNKNOWN"
    if hasattr(v, "value"):
        v = v.value
    return str(v).upper()


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {str(v).strip().upper() for v in (values or ()) if str(v).strip()}


def _clean_needle(value: str | None) -> str | None:
    text = str(value or "").strip()
    return text or None


def _gate_summary(row: StrategyRunResult) -> dict[str, Any]:
    gate = getattr(row, "gate_summary", None)
    if gate is None:
        data: dict[str, Any] = {}
    else:
        data = gate.model_dump(mode="json") if hasattr(gate, "model_dump") else dict(gate)
    # Preserve richer per-strategy gate statuses when older summary artifacts have
    # sparse/default gate_summary fields but row-level forensic fields are present.
    row_gate_pairs = {
        "robustness_gate": getattr(row, "robustness_gate_status", None),
        "cpcv_robustness_gate": getattr(row, "cpcv_robustness_gate_status", None),
        "execution_realism_gate": getattr(row, "execution_realism_gate", None)
        or getattr(row, "execution_realism_status", None),
        "data_quality_gate": getattr(row, "data_quality_gate_status", None),
        "market_data_integrity_gate": getattr(row, "market_data_integrity_gate_status", None),
        "parameter_sensitivity_gate": getattr(row, "parameter_sensitivity_gate_status", None),
        "regime_analysis_gate": getattr(row, "regime_analysis_gate_status", None),
        "adjudication_gate": getattr(row, "adjudication_status", None),
    }
    for key, value in row_gate_pairs.items():
        if value and _upper(data.get(key)) in {"UNKNOWN", "NOT_RUN", "NOT_INVOKED"}:
            data[key] = _upper(value)
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
        "market_data_integrity": getattr(row, "market_data_integrity_artifact_path", None),
        "data_quality": getattr(row, "data_quality_artifact_path", None),
        "parameter_sensitivity": getattr(row, "parameter_sensitivity_artifact_path", None),
        "regime_analysis": getattr(row, "regime_analysis_artifact_path", None),
        "trade_markers": getattr(row, "trade_markers_path", None),
    }
    observed = {
        "evidence_manifest": getattr(row, "evidence_manifest_sha256", None),
        "robustness": getattr(row, "robustness_evidence_sha256", None),
        "cpcv": getattr(row, "cpcv_evidence_sha256", None),
        "market_data_integrity": getattr(row, "market_data_integrity_evidence_sha256", None),
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


def _contains_any(values: list[str], needle: str | None) -> bool:
    if not needle:
        return True
    hay = "\n".join(str(v) for v in values).lower()
    return needle.lower() in hay


def _matches(
    row: BacktestForensicStrategyRow,
    *,
    review_posture: set[str],
    status: set[str],
    risk_flag: set[str],
    data_plane: set[str],
    promotion_eligible: bool | None,
    strategy_id_contains: str | None,
    blocker_contains: str | None,
    warning_contains: str | None,
) -> bool:
    if review_posture and _upper(row.review_posture) not in review_posture:
        return False
    if status and _upper(row.status) not in status:
        return False
    if risk_flag and not risk_flag.intersection({_upper(flag) for flag in row.risk_flags}):
        return False
    if data_plane and _upper(row.data_plane) not in data_plane:
        return False
    if promotion_eligible is not None and bool(row.promotion_eligible) is not bool(promotion_eligible):
        return False
    if strategy_id_contains and strategy_id_contains.lower() not in row.strategy_id.lower():
        return False
    if not _contains_any(row.blockers + row.promotion_blocked_reasons, blocker_contains):
        return False
    if not _contains_any(row.warnings, warning_contains):
        return False
    return True


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
        review_ready_count=sum(1 for r in rows if r.review_posture == "REVIEW_READY"),
        synthetic_count=sum(1 for r in rows if r.data_plane == "SYNTHETIC"),
        provider_snapshot_count=sum(1 for r in rows if r.data_plane == "PROVIDER_SNAPSHOT"),
        real_local_count=sum(1 for r in rows if r.data_plane == "REAL_LOCAL"),
        warning_count=sum(len(r.warnings) for r in rows),
        blocker_count=sum(len(r.blockers) + len(r.promotion_blocked_reasons) for r in rows),
        risk_flag_counts=dict(sorted(flag_counter.items())),
        review_posture_counts=dict(sorted(Counter(r.review_posture for r in rows).items())),
        status_counts=dict(sorted(Counter(r.status for r in rows).items())),
        data_plane_counts=dict(sorted(Counter(r.data_plane for r in rows).items())),
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


def _bounded_limit(limit: int) -> int:
    try:
        value = int(limit)
    except (TypeError, ValueError):
        value = 200
    return max(1, min(value, 1000))


def _payload(
    path: Path | None,
    summary: StrategyBatchRunSummary | None,
    *,
    repo_root: Path | None,
    route: str,
    review_posture: tuple[str, ...] | list[str] = (),
    status: tuple[str, ...] | list[str] = (),
    risk_flag: tuple[str, ...] | list[str] = (),
    data_plane: tuple[str, ...] | list[str] = (),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    degraded: list[str] = []
    if path is None or summary is None:
        degraded.append("NO_BATCH_ARTIFACTS" if route.endswith("latest") else "BATCH_NOT_FOUND")
    all_rows = [_forensic_row(row) for row in (summary.strategies if summary else [])]
    posture_filter = _norm_set(review_posture)
    status_filter = _norm_set(status)
    risk_filter = _norm_set(risk_flag)
    data_filter = _norm_set(data_plane)
    strategy_needle = _clean_needle(strategy_id_contains)
    blocker_needle = _clean_needle(blocker_contains)
    warning_needle = _clean_needle(warning_contains)
    filtered = [
        row
        for row in all_rows
        if _matches(
            row,
            review_posture=posture_filter,
            status=status_filter,
            risk_flag=risk_filter,
            data_plane=data_filter,
            promotion_eligible=promotion_eligible,
            strategy_id_contains=strategy_needle,
            blocker_contains=blocker_needle,
            warning_contains=warning_needle,
        )
    ]
    returned = filtered[: _bounded_limit(limit)]
    replay = latest_replay_verification_summary(repo_root=repo_root)
    replay_posture = _replay_evidence_status(replay)
    return BacktestForensicsPayload(
        scan_root=str(_default_scan_root(repo_root)),
        summary_path=str(path) if path else None,
        degraded=degraded,
        batch=_batch_overview(summary),
        summary=_summary(summary, all_rows),
        filtered_summary=_summary(summary, filtered),
        strategies=returned,
        total_strategy_count=len(all_rows),
        filtered_strategy_count=len(filtered),
        returned_strategy_count=len(returned),
        filters={
            "review_posture": sorted(posture_filter),
            "status": sorted(status_filter),
            "risk_flag": sorted(risk_filter),
            "data_plane": sorted(data_filter),
            "promotion_eligible": promotion_eligible,
            "strategy_id_contains": strategy_needle,
            "blocker_contains": blocker_needle,
            "warning_contains": warning_needle,
            "limit": _bounded_limit(limit),
        },
        raw_strategy_batch_route=route,
        artifact_replay={
            **replay,
            "replay_evidence_status": replay_posture["status"],
            "replay_evidence_blocked": replay_posture["blocked"],
        },
        guardrails=[
            "Read-plane forensic review only.",
            "No strategy promotion, adjudication, order submission, or live-trading authorization is granted.",
            "Promotion-ready means evidence appears present; validator/orchestrator authority is still required.",
            "Synthetic or paper-only strategies remain research evidence only.",
        ],
    ).model_dump(mode="json")


def build_ui_backtest_forensics_latest_payload(
    *,
    repo_root: Path | None = None,
    review_posture: tuple[str, ...] | list[str] = (),
    status: tuple[str, ...] | list[str] = (),
    risk_flag: tuple[str, ...] | list[str] = (),
    data_plane: tuple[str, ...] | list[str] = (),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    path, summary = discover_latest_batch_summary(repo_root=repo_root)
    return _payload(
        path,
        summary,
        repo_root=repo_root,
        route="/ui/strategy-batches/latest",
        review_posture=review_posture,
        status=status,
        risk_flag=risk_flag,
        data_plane=data_plane,
        promotion_eligible=promotion_eligible,
        strategy_id_contains=strategy_id_contains,
        blocker_contains=blocker_contains,
        warning_contains=warning_contains,
        limit=limit,
    )


def build_ui_backtest_forensics_detail_payload(
    run_id: str,
    *,
    repo_root: Path | None = None,
    review_posture: tuple[str, ...] | list[str] = (),
    status: tuple[str, ...] | list[str] = (),
    risk_flag: tuple[str, ...] | list[str] = (),
    data_plane: tuple[str, ...] | list[str] = (),
    promotion_eligible: bool | None = None,
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    path, summary = discover_batch_by_run_id(run_id, repo_root=repo_root)
    return _payload(
        path,
        summary,
        repo_root=repo_root,
        route=f"/ui/strategy-batches/{run_id}",
        review_posture=review_posture,
        status=status,
        risk_flag=risk_flag,
        data_plane=data_plane,
        promotion_eligible=promotion_eligible,
        strategy_id_contains=strategy_id_contains,
        blocker_contains=blocker_contains,
        warning_contains=warning_contains,
        limit=limit,
    )


__all__ = ["build_ui_backtest_forensics_detail_payload", "build_ui_backtest_forensics_latest_payload"]
