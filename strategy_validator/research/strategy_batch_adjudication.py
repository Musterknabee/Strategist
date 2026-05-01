"""Optional orchestrator adjudication adapter (commit=False; no batch→ledger coupling)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from strategy_validator.contracts.evidence import Evidence, EvidenceBundle, ReproducibilityManifest
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.strategy_batch import StrategyBatchSpec, StrategyCandidateSpec
from strategy_validator.core.enums import EvidenceType, PromotionState
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256
from strategy_validator.validator.orchestrator import adjudicate
from strategy_validator.validator.readiness import perform_readiness_check


def _demo_repro(evidence_manifest_sha256: str) -> ReproducibilityManifest:
    b = evidence_manifest_sha256
    if len(b) < 32:
        b = (b * 4)[:32]

    def _field(i: int) -> str:
        return canonical_json_sha256({"i": i, "b": b})[:32]

    return ReproducibilityManifest(
        code_hash=_field(0),
        data_snapshot_hash=_field(1),
        universe_hash=_field(2),
        feature_graph_hash=_field(3),
        parameter_manifest_hash=_field(4),
        benchmark_version="bench-v1",
        cost_model_version="v1",
        calendar_version="v1",
    )


def adjudicate_strategy_run_demo(
    *,
    candidate: StrategyCandidateSpec,
    batch: StrategyBatchSpec,
    run_dir: str | Path,
    metrics: dict[str, float],
    evidence_manifest_sha256: str,
) -> tuple[str, list[str]]:
    """Invoke :func:`adjudicate` with ``commit=False``; persist JSON summary under *run_dir*.

    Returns ``(adjudication_gate_status, extra_warnings)``.
    """

    strat_dir = Path(run_dir)
    bundle = EvidenceBundle(
        reproducibility=_demo_repro(evidence_manifest_sha256),
        benchmark_rung="L1",
        search_breadth=1,
        evaluation_time_utc=candidate.as_of_utc,
        market_data_subject_id="SYNTHETIC_DEMO_SUBJECT",
        semantic_artifacts=[],
    )
    experiment = ExperimentManifest(
        experiment_id=f"batch-{batch.batch_id}-{candidate.strategy_id}",
        strategy_name=candidate.strategy_type,
        version="0.0.0-demo",
        proposer_id="strategy_batch_runner",
        state=PromotionState.INVALID,
        evidence_bundle=bundle,
    )
    sr = float(metrics.get("total_return", 0.0))
    br = 0.0
    evidence_items = (
        Evidence(
            evidence_id=f"{candidate.strategy_id}-bench",
            experiment_id=experiment.experiment_id,
            evidence_type=EvidenceType.BACKTEST_LOG,
            payload={
                "benchmark_id": "SPY",
                "benchmark_version": "bench-v1",
                "strategy_return": sr,
                "benchmark_return": br,
                "benchmark_delta": sr - br,
                "benchmark_passed": True,
                "horizon": "strategy_batch_demo",
                "schema_version": "strategy_batch_demo_evidence/v1",
            },
            source_module="strategy_validator.research.strategy_batch_adjudication",
            checksum=canonical_json_sha256({"id": candidate.strategy_id, "m": metrics}),
        ),
    )
    warnings: list[str] = []
    try:
        state = adjudicate(
            experiment,
            evidence_items,
            commit=False,
            readiness_report=perform_readiness_check(),
        )
    except Exception as exc:  # AdjudicationError or gate failures surfaced as exceptions
        payload = {
            "ok": False,
            "error": type(exc).__name__,
            "message": str(exc),
            "promotion_state": None,
        }
        (strat_dir / "adjudication_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return "BLOCKED", [f"ADJUDICATION_EXCEPTION:{type(exc).__name__}"]

    payload = {
        "ok": True,
        "promotion_state": state.value if hasattr(state, "value") else str(state),
        "synthetic_demo": True,
        "may_gate_live_promotion": False,
    }
    (strat_dir / "adjudication_result.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if state in (PromotionState.PROMOTABLE, PromotionState.CONDITIONAL):
        warnings.append("ORCHESTRATOR_STATE_NON_REJECTED_BUT_SYNTHETIC_STILL_PAPER_ONLY")
    return "COMPLETED", warnings


def build_adjudication_hook() -> Any:
    """Return a callable compatible with :func:`run_strategy_batch` ``adjudication_hook``."""

    def _hook(**kwargs: Any) -> tuple[str, list[str]]:
        return adjudicate_strategy_run_demo(**kwargs)

    return _hook


__all__ = ["adjudicate_strategy_run_demo", "build_adjudication_hook"]
