"""Deterministic thesis/falsification evaluator (no live trading)."""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult
from strategy_validator.contracts.strategy_thesis import (
    FalsificationCriterion,
    StrategyThesis,
    ThesisEvaluation,
    ThesisSupportStatus,
)


def strategy_thesis_root_directory(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_STRATEGY_THESIS_ROOT", "").strip()
    if raw:
        p = Path(raw)
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    return (artifact_root_directory(repo_root) / "strategy_theses").resolve()


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def finalize_thesis(thesis: StrategyThesis) -> StrategyThesis:
    return thesis.model_copy(update={"thesis_sha256": _sha(thesis.model_dump(mode="json", exclude={"thesis_sha256"}))})


def finalize_evaluation(evaluation: ThesisEvaluation) -> ThesisEvaluation:
    return evaluation.model_copy(update={"evaluation_sha256": _sha(evaluation.model_dump(mode="json", exclude={"evaluation_sha256"}))})


def _metric_value(result: StrategyRunResult, metric: str) -> Any:
    if hasattr(result, metric):
        return getattr(result, metric)
    if metric.startswith("gate_summary."):
        return getattr(result.gate_summary, metric.split(".", 1)[1], None)
    if metric in result.metrics:
        return result.metrics[metric]
    return None


def _criterion_triggered(result: StrategyRunResult, criterion: FalsificationCriterion) -> bool:
    actual = _metric_value(result, criterion.metric)
    if actual is None:
        return False
    op = criterion.operator
    threshold = criterion.threshold
    try:
        if op == "lt":
            return actual < threshold
        if op == "lte":
            return actual <= threshold
        if op == "gt":
            return actual > threshold
        if op == "gte":
            return actual >= threshold
        if op == "eq":
            return actual == threshold
    except TypeError:
        return False
    return False


def _find_result(summary: StrategyBatchRunSummary, strategy_id: str) -> StrategyRunResult | None:
    for result in summary.strategies:
        if result.strategy_id == strategy_id:
            return result
    return None


def evaluate_strategy_thesis(
    *,
    thesis: StrategyThesis,
    batch_summary: StrategyBatchRunSummary,
    output_root: Path | None = None,
    repo_root: Path | None = None,
) -> ThesisEvaluation:
    result = _find_result(batch_summary, thesis.strategy_id)
    missing: list[str] = []
    contradictions: list[str] = []
    falsified: list[FalsificationCriterion] = []
    refs: list[dict[str, Any]] = []
    summary: dict[str, Any] = {"batch_id": batch_summary.batch_id, "run_id": batch_summary.run_id}

    if result is None:
        evaluation = ThesisEvaluation(
            thesis_id=thesis.thesis_id,
            strategy_id=thesis.strategy_id,
            support_status=ThesisSupportStatus.INCONCLUSIVE,
            missing_evidence=["STRATEGY_RESULT_MISSING"],
            evidence_summary=summary,
        )
        return finalize_evaluation(evaluation)

    if result.evidence_manifest_path:
        refs.append({"ref_kind": "strategy_evidence_manifest", "artifact_path": result.evidence_manifest_path, "sha256": result.evidence_manifest_sha256})
    if result.data_snapshot_manifest_path:
        refs.append({"ref_kind": "data_snapshot_manifest", "artifact_path": result.data_snapshot_manifest_path, "sha256": result.data_snapshot_manifest_sha256})

    for req in thesis.required_evidence:
        if not req.required:
            continue
        kind = req.evidence_kind
        if kind == "robustness" and not result.robustness_evidence_sha256:
            missing.append(req.requirement_id)
        if kind == "execution_realism" and not result.execution_realism_digest:
            missing.append(req.requirement_id)
        if kind == "provider_snapshot" and not result.provider_snapshot_manifest_sha256:
            missing.append(req.requirement_id)
        if kind == "scorecard" and not result.strategy_scorecard_path:
            missing.append(req.requirement_id)

    for criterion in thesis.falsification_criteria:
        if _criterion_triggered(result, criterion):
            falsified.append(criterion)
            contradictions.append(f"FALSIFICATION_TRIGGERED:{criterion.criterion_id}:{criterion.metric}")

    if result.data_plane == "SYNTHETIC":
        contradictions.append("SYNTHETIC_DATA_CANNOT_STRONGLY_SUPPORT_THESIS")

    support = ThesisSupportStatus.INCONCLUSIVE
    if falsified:
        support = ThesisSupportStatus.FALSIFIED
    elif missing:
        support = ThesisSupportStatus.INCONCLUSIVE
    elif result.data_plane == "SYNTHETIC":
        support = ThesisSupportStatus.INCONCLUSIVE
    elif result.gate_summary.promotion_eligible and result.status.value == "PASSED":
        support = ThesisSupportStatus.SUPPORTED
    elif result.status.value in {"PASSED", "PAPER_ONLY"}:
        support = ThesisSupportStatus.WEAKLY_SUPPORTED

    summary.update(
        {
            "status": result.status.value,
            "data_plane": result.data_plane,
            "promotion_eligible": result.gate_summary.promotion_eligible,
            "total_return": result.total_return,
            "max_drawdown": result.max_drawdown,
            "sharpe_like": result.sharpe_like,
            "provider_snapshot_manifest_sha256": result.provider_snapshot_manifest_sha256,
        }
    )
    evaluation = ThesisEvaluation(
        thesis_id=thesis.thesis_id,
        strategy_id=thesis.strategy_id,
        support_status=support,
        evidence_refs=refs,
        contradictions=contradictions,
        missing_evidence=missing,
        falsified_criteria=falsified,
        triggered_kill_criteria=[c.criterion_id for c in falsified if c.hard_kill],
        evidence_summary=summary,
    )
    evaluation = finalize_evaluation(evaluation)
    root = output_root or strategy_thesis_root_directory(repo_root)
    sroot = root / thesis.strategy_id
    thesis = finalize_thesis(thesis)
    _write(sroot / "thesis.json", thesis.model_dump(mode="json"))
    _write(sroot / "thesis_evaluation.json", evaluation.model_dump(mode="json"))
    _write(root / "latest" / "thesis_evaluation.json", evaluation.model_dump(mode="json"))
    return evaluation


def evaluate_from_paths(*, strategy_run: Path, thesis_path: Path, output_root: Path | None = None) -> ThesisEvaluation:
    summary_path = strategy_run / "batch_summary.json" if strategy_run.is_dir() else strategy_run
    summary = StrategyBatchRunSummary.model_validate(_read(summary_path))
    thesis = finalize_thesis(StrategyThesis.model_validate(_read(thesis_path)))
    return evaluate_strategy_thesis(thesis=thesis, batch_summary=summary, output_root=output_root)


def build_ui_strategy_thesis_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = strategy_thesis_root_directory(repo_root)
    latest = root / "latest" / "thesis_evaluation.json"
    degraded: list[str] = []
    payload: dict[str, Any] | None = None
    if not latest.is_file():
        degraded.append("NO_THESIS_EVALUATION")
    else:
        try:
            payload = _read(latest)
        except Exception:
            degraded.append("THESIS_EVALUATION_UNREADABLE")
    return {
        "schema_version": "ui_strategy_thesis/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "scan_root": str(root),
        "latest_path": str(latest),
        "degraded": degraded,
        "latest": payload,
    }


def list_thesis_evaluations(*, repo_root: Path | None = None) -> list[dict[str, Any]]:
    root = strategy_thesis_root_directory(repo_root)
    rows: list[dict[str, Any]] = []
    if not root.is_dir():
        return rows
    for path in sorted(root.glob("*/thesis_evaluation.json"), key=lambda p: p.stat().st_mtime, reverse=True):
        try:
            rows.append(_read(path))
        except Exception:
            continue
    return rows


__all__ = [
    "build_ui_strategy_thesis_latest_payload",
    "evaluate_from_paths",
    "evaluate_strategy_thesis",
    "finalize_evaluation",
    "finalize_thesis",
    "list_thesis_evaluations",
    "strategy_thesis_root_directory",
]
