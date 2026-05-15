"""Deterministic Oracle strategy thesis generation from batch evidence.

The Oracle may propose advisory theses from evidence, but this module deliberately
stays read-plane/paper-only: no live trading, no ledger mutation, no capital authority.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.strategy_batch import StrategyBatchRunSummary, StrategyRunResult
from strategy_validator.contracts.strategy_thesis import (
    ExpectedEdge,
    ExpectedFailureMode,
    FalsificationCriterion,
    GeneratedStrategyThesisArtifact,
    StrategyThesis,
    StrategyThesisGenerationReport,
    ThesisEvidenceRequirement,
    ThesisSupportStatus,
)
from strategy_validator.research.strategy_thesis_eval import (
    evaluate_strategy_thesis,
    finalize_thesis,
    strategy_thesis_root_directory,
)


def _sha(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()).hexdigest()


def _read(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _write(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")


def finalize_generation_report(report: StrategyThesisGenerationReport) -> StrategyThesisGenerationReport:
    return report.model_copy(update={"report_sha256": _sha(report.model_dump(mode="json", exclude={"report_sha256"}))})


def _family_for(strategy_type: str | None) -> tuple[str, str, str, list[str], list[str]]:
    st = strategy_type or "unknown"
    if "bearish" in st or "breakdown" in st:
        return (
            "risk-off distribution",
            "Weakening participation near highs may precede downside or hedge-worthy breakdown after evidence gates.",
            "Distribution, failed upside auctions, and deteriorating breadth may create asymmetric downside pressure.",
            ["DISTRIBUTION", "RISK_OFF", "LIQUID"],
            ["short squeeze", "policy shock", "broad risk-on reversal"],
        )
    if "reversion" in st or "reversal" in st or "gap_fill" in st or "hammer" in st:
        return (
            "overextension reversion",
            "Short-horizon dislocations may mean-revert after risk, liquidity, and data-quality controls.",
            "Temporary liquidity imbalance or behavioral overreaction may push price away from local fair value.",
            ["RANGE_BOUND", "LIQUID", "STABLE_VOLATILITY"],
            ["strong directional trend", "structural break", "news gap"],
        )
    if "squeeze" in st or "volatility" in st:
        return (
            "volatility expansion",
            "Compression followed by expansion may produce asymmetric continuation after costs.",
            "Latent order-flow imbalance can remain hidden during low volatility and express during breakout.",
            ["COMPRESSED_VOLATILITY", "BREAKOUT_CANDIDATE", "LIQUID"],
            ["false breakout", "spread widening", "low participation"],
        )
    if "breakout" in st or "trend" in st or "momentum" in st or "continuation" in st or "gap_and_go" in st:
        return (
            "trend persistence",
            "Positive serial dependence may persist after point-in-time and execution-realism controls.",
            "Delayed risk repricing and institutional flow persistence can create continuation pressure.",
            ["TRENDING", "LIQUID", "ORDERLY_VOLATILITY"],
            ["flat/choppy regime", "mean-reverting shock", "liquidity withdrawal"],
        )
    return (
        "evidence-selected technical edge",
        "The strategy may exhibit repeatable paper/research edge only if PIT, robustness, and execution evidence survive.",
        "A persistent behavioral or microstructure effect may exist, but it must be proven by evidence rather than assumed.",
        ["UNKNOWN_REGIME"],
        ["insufficient evidence", "regime instability", "execution drag"],
    )


def _drawdown_kill(result: StrategyRunResult) -> float:
    observed = abs(float(result.max_drawdown or 0.25))
    return max(0.08, round(observed * 1.5, 6))


def build_strategy_thesis_from_result(
    *,
    result: StrategyRunResult,
    batch_summary: StrategyBatchRunSummary,
    now_utc: datetime | None = None,
) -> StrategyThesis:
    """Create a falsification-first StrategyThesis from one batch result."""
    t = now_utc or datetime.now(timezone.utc)
    st = result.strategy_type or "unknown"
    family, rationale, inefficiency, regimes, failure_regimes = _family_for(st)
    minimum_days = max(30, min(365, int(result.bars_row_count or 30)))
    thesis_id = f"oracle-generated:{batch_summary.run_id}:{result.strategy_id}"
    hypothesis = (
        f"{result.strategy_id} ({st}) expresses a {family} hypothesis: it should retain positive "
        "paper/research edge only when point-in-time data, robustness, execution-realism, "
        "and market-data integrity evidence remain intact."
    )
    required_evidence = [
        ThesisEvidenceRequirement(
            requirement_id="REQ_SCORECARD_EVIDENCE",
            evidence_kind="scorecard",
            description="Strategy scorecard/evidence bundle must exist for operator review.",
        ),
        ThesisEvidenceRequirement(
            requirement_id="REQ_ROBUSTNESS_EVIDENCE",
            evidence_kind="robustness",
            description="Walk-forward or CPCV robustness evidence must be present.",
        ),
        ThesisEvidenceRequirement(
            requirement_id="REQ_EXECUTION_REALISM_EVIDENCE",
            evidence_kind="execution_realism",
            description="Estimated fees/slippage/capacity evidence must be present.",
        ),
    ]
    if result.provider_snapshot_manifest_sha256:
        required_evidence.append(
            ThesisEvidenceRequirement(
                requirement_id="REQ_PROVIDER_SNAPSHOT_EVIDENCE",
                evidence_kind="provider_snapshot",
                description="Provider snapshot lineage must remain digest-addressed.",
            )
        )

    falsification = [
        FalsificationCriterion(
            criterion_id="KILL_TOTAL_RETURN_NON_POSITIVE",
            metric="total_return",
            operator="lte",
            threshold=0.0,
            description="Generated thesis is falsified if observed paper/research total return is non-positive.",
            hard_kill=True,
        ),
        FalsificationCriterion(
            criterion_id="KILL_PROMOTION_INELIGIBLE",
            metric="gate_summary.promotion_eligible",
            operator="eq",
            threshold=False,
            description="Generated thesis is falsified for promotion purposes if promotion eligibility is false.",
            hard_kill=True,
        ),
        FalsificationCriterion(
            criterion_id="WATCH_DRAWDOWN_EXCESS",
            metric="max_drawdown",
            operator="lt",
            threshold=-_drawdown_kill(result),
            description="Drawdown outside the observed evidence envelope requires operator review.",
            hard_kill=False,
        ),
    ]
    return finalize_thesis(
        StrategyThesis(
            strategy_id=result.strategy_id,
            thesis_id=thesis_id,
            hypothesis=hypothesis,
            economic_rationale=rationale,
            market_inefficiency=inefficiency,
            expected_regimes=regimes,
            expected_failure_regimes=[
                ExpectedFailureMode(
                    regime=regime,
                    description=f"Oracle expects {result.strategy_id} to degrade in {regime}.",
                    expected_symptom="negative total_return, weak robustness, or promotion gate block",
                )
                for regime in failure_regimes
            ],
            expected_edge=ExpectedEdge(
                description="Positive total_return after PIT, robustness, and execution-realism controls.",
                expected_metric="total_return",
                expected_direction="positive",
                minimum_evidence_days=minimum_days,
            ),
            required_evidence=required_evidence,
            falsification_criteria=falsification,
            author="oracle_deterministic_thesis_generator",
            created_at_utc=t,
        )
    )


def _candidate_mutations(result: StrategyRunResult) -> list[str]:
    mutations: list[str] = []
    if result.total_return is not None and result.total_return > 0:
        mutations.append("Test adjacent parameter bands and require the same edge direction under parameter_sensitivity gate.")
    if result.max_drawdown is not None and result.max_drawdown < -0.05:
        mutations.append("Add stricter volatility/drawdown overlay before any paper-promotion review.")
    if result.market_data_integrity_gate_status == "WARNING":
        mutations.append("Re-run against higher-trust provider snapshot before increasing confidence.")
    if result.robustness_gate_status not in {"PROVEN", "PASS"}:
        mutations.append("Extend lookback or fold count before treating the thesis as supported.")
    if not mutations:
        mutations.append("Keep baseline thesis unchanged; next action is out-of-sample paper replay.")
    return mutations


def generate_strategy_theses(
    *,
    batch_summary: StrategyBatchRunSummary,
    source_batch_summary_path: Path,
    output_root: Path | None = None,
    evaluate: bool = True,
    now_utc: datetime | None = None,
) -> StrategyThesisGenerationReport:
    root = output_root or strategy_thesis_root_directory()
    generation_root = root / "generated" / batch_summary.run_id
    artifacts: list[GeneratedStrategyThesisArtifact] = []
    warnings: list[str] = []
    evaluated_count = 0
    t = now_utc or datetime.now(timezone.utc)

    for result in batch_summary.strategies:
        if result.status.value in {"FAILED", "BLOCKED"}:
            warnings.append(f"GENERATED_FOR_NON_PASSING_RESULT:{result.strategy_id}:{result.status.value}")
        thesis = build_strategy_thesis_from_result(result=result, batch_summary=batch_summary, now_utc=t)
        thesis_path = generation_root / result.strategy_id / "thesis.json"
        _write(thesis_path, thesis.model_dump(mode="json"))
        support_status: ThesisSupportStatus | None = None
        evaluation_path: str | None = None
        evaluation_sha256: str | None = None
        if evaluate:
            evaluation = evaluate_strategy_thesis(
                thesis=thesis,
                batch_summary=batch_summary,
                output_root=root,
                repo_root=None,
            )
            evaluated_count += 1
            support_status = evaluation.support_status
            evaluation_path = str(root / result.strategy_id / "thesis_evaluation.json")
            evaluation_sha256 = evaluation.evaluation_sha256

        artifacts.append(
            GeneratedStrategyThesisArtifact(
                strategy_id=result.strategy_id,
                strategy_type=result.strategy_type,
                thesis_id=thesis.thesis_id,
                thesis_path=str(thesis_path),
                thesis_sha256=thesis.thesis_sha256,
                support_status=support_status,
                evaluation_path=evaluation_path,
                evaluation_sha256=evaluation_sha256,
                generated_from_status=result.status.value,
                promotion_eligible=result.gate_summary.promotion_eligible,
                expected_primary_edge=thesis.expected_edge.expected_metric,
                candidate_mutations=_candidate_mutations(result),
                operator_actions=[
                    "Review generated thesis before using it as research doctrine.",
                    "Run out-of-sample paper replay before promotion consideration.",
                ],
            )
        )

    report = StrategyThesisGenerationReport(
        batch_id=batch_summary.batch_id,
        run_id=batch_summary.run_id,
        generated_at_utc=t,
        source_batch_summary_path=str(source_batch_summary_path),
        generated_count=len(artifacts),
        evaluated_count=evaluated_count,
        generated_theses=artifacts,
        warnings=warnings,
        operator_actions=[
            "Treat generated theses as Oracle advisory hypotheses only.",
            "Do not enable live trading from generated theses without validator/orchestrator approval.",
            "Promote only after independent out-of-sample evidence and operator review.",
        ],
    )
    report = finalize_generation_report(report)
    _write(generation_root / "thesis_generation_report.json", report.model_dump(mode="json"))
    _write(root / "latest" / "thesis_generation_report.json", report.model_dump(mode="json"))
    return report


def generate_from_paths(*, strategy_run: Path, output_root: Path | None = None, evaluate: bool = True) -> StrategyThesisGenerationReport:
    summary_path = strategy_run / "batch_summary.json" if strategy_run.is_dir() else strategy_run
    summary = StrategyBatchRunSummary.model_validate(_read(summary_path))
    return generate_strategy_theses(
        batch_summary=summary,
        source_batch_summary_path=summary_path,
        output_root=output_root,
        evaluate=evaluate,
    )


def build_ui_strategy_thesis_generation_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    root = strategy_thesis_root_directory(repo_root)
    latest = root / "latest" / "thesis_generation_report.json"
    degraded: list[str] = []
    payload: dict[str, Any] | None = None
    if not latest.is_file():
        degraded.append("NO_THESIS_GENERATION_REPORT")
    else:
        try:
            payload = _read(latest)
        except Exception:
            degraded.append("THESIS_GENERATION_REPORT_UNREADABLE")
    return {
        "schema_version": "ui_strategy_thesis_generation/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "scan_root": str(root),
        "latest_path": str(latest),
        "degraded": degraded,
        "latest_generation": payload,
    }


__all__ = [
    "build_strategy_thesis_from_result",
    "build_ui_strategy_thesis_generation_latest_payload",
    "finalize_generation_report",
    "generate_from_paths",
    "generate_strategy_theses",
]
