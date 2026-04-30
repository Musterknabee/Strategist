from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime

from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import AdjudicationDecision, ExperimentManifest, GateResult
from strategy_validator.core.config import load_config
from strategy_validator.core.enums import PromotionState, RuntimeMode
from strategy_validator.core.exceptions import AdjudicationError
from strategy_validator.ledger.writer import commit_state_transition, issue_write_authority
from strategy_validator.validator.orchestrator.benchmark_context_policy import evaluate_benchmark_context_gate
from strategy_validator.validator.orchestrator.benchmark_policy import evaluate_benchmark_performance_gate
from strategy_validator.validator.orchestrator.decoy_policy import evaluate_decoy_survival_gate
from strategy_validator.validator.orchestrator.evidence_gates import _materialize_decoy_hook
from strategy_validator.validator.orchestrator.execution_policy import evaluate_execution_constraint_gates
from strategy_validator.validator.orchestrator.execution_realism import (
    _evaluate_execution_realism,
    _evaluate_snapshot_freshness,
)
from strategy_validator.validator.orchestrator.integrity_policy import evaluate_evidence_integrity_gates
from strategy_validator.validator.orchestrator.market_data_policy import evaluate_market_data_source_policy
from strategy_validator.validator.orchestrator.robustness_policy import evaluate_robustness_gate
from strategy_validator.validator.orchestrator.semantic_policy import evaluate_semantic_gates
from strategy_validator.validator.readiness import perform_readiness_check

_DEPLOYMENT_ONLY_BLOCKER_CODES = frozenset(
    {
        "MISSING_PRODUCTION_TOKEN",
        "PLACEHOLDER_PRODUCTION_TOKEN",
        "INSUFFICIENT_TOKEN_SCOPES",
        "INCOMPATIBLE_SCHEMA",
        "LEDGER_SCHEMA_NOT_CURRENT",
        "LEDGER_DATABASE_MISSING",
    }
)


def _reproducibility_gate(experiment: ExperimentManifest) -> GateResult:
    repro = getattr(experiment.evidence_bundle, "reproducibility", None)
    required = (
        "code_hash",
        "data_snapshot_hash",
        "universe_hash",
        "feature_graph_hash",
        "parameter_manifest_hash",
        "benchmark_version",
        "cost_model_version",
        "calendar_version",
    )
    ok = repro is not None and all(getattr(repro, field, None) for field in required)
    return GateResult(
        gate_name="ReproducibilityContract",
        passed=ok,
        reason=None if ok else "MISSING_REPRODUCIBILITY_MANIFEST",
    )


def adjudicate(
    experiment: ExperimentManifest,
    evidence: Iterable[Evidence] | None = None,
    *,
    liquidity_feed=None,
    borrow_feed=None,
    liquidity_fallback_feed=None,
    borrow_fallback_feed=None,
    commit: bool = True,
    created_at: datetime | None = None,
    readiness_report=None,
) -> PromotionState:
    cfg = load_config()
    working_experiment = experiment.model_copy(deep=True)
    readiness = readiness_report or perform_readiness_check()
    evidence_items = tuple(evidence or ())
    previous_state = working_experiment.state
    state = PromotionState.PROMOTABLE
    gate_results: list[GateResult] = []
    summary_notes: list[str] = [f"Runtime readiness at decision time: {readiness.status}."]

    readiness_blockers = tuple(readiness.blockers or ())
    adjudication_blockers = tuple(
        blocker for blocker in readiness_blockers if blocker.code not in _DEPLOYMENT_ONLY_BLOCKER_CODES
    )
    deployment_only_blockers = tuple(
        blocker for blocker in readiness_blockers if blocker.code in _DEPLOYMENT_ONLY_BLOCKER_CODES
    )
    runtime_ok = readiness.run_mode != RuntimeMode.PRODUCTION or not adjudication_blockers
    gate_results.append(
        GateResult(
            gate_name="RuntimeReadiness",
            passed=runtime_ok,
            reason=None if runtime_ok else ";".join(item.code for item in adjudication_blockers) or "READINESS_BLOCKED",
        )
    )
    if deployment_only_blockers:
        summary_notes.append(
            "Deployment-only readiness blockers observed: "
            + ", ".join(item.code for item in deployment_only_blockers)
            + "."
        )
    if readiness.run_mode == RuntimeMode.PRODUCTION and not runtime_ok:
        raise AdjudicationError(
            "Production adjudication blocked by readiness: " + ", ".join(item.code for item in adjudication_blockers)
        )
    if not runtime_ok:
        state = PromotionState.CONDITIONAL

    repro_gate = _reproducibility_gate(working_experiment)
    gate_results.append(repro_gate)
    if not repro_gate.passed:
        state = PromotionState.INVALID

    _materialize_decoy_hook(working_experiment, evidence_items)

    benchmark_context = evaluate_benchmark_context_gate(working_experiment, evidence_items)
    gate_results.append(benchmark_context)
    if not benchmark_context.passed:
        state = PromotionState.REJECTED

    execution_report = _evaluate_execution_realism(
        evidence_items,
        600.0,
        evaluation_time_utc=working_experiment.evidence_bundle.evaluation_time_utc,
        market_data_subject_id=working_experiment.evidence_bundle.market_data_subject_id,
        liquidity_feed=liquidity_feed,
        borrow_feed=borrow_feed,
        liquidity_fallback_feed=liquidity_fallback_feed,
        borrow_fallback_feed=borrow_fallback_feed,
        policy=cfg.runtime_policy,
    )
    execution_outcome = evaluate_execution_constraint_gates(execution_report, state=state)
    state = execution_outcome.state
    gate_results.extend(execution_outcome.gates)
    summary_notes.extend(execution_outcome.summary_notes)

    benchmark_outcome = evaluate_benchmark_performance_gate(
        working_experiment,
        evidence_items,
        context_passed=benchmark_context.passed,
        total_post_cost_bps=float(execution_report.total_post_cost_bps or 0.0),
        state=state,
    )
    state = benchmark_outcome.state
    gate_results.append(benchmark_outcome.gate)

    integrity_outcome = evaluate_evidence_integrity_gates(evidence_items, state=state)
    state = integrity_outcome.state
    gate_results.extend(integrity_outcome.gates)

    semantic_outcome = evaluate_semantic_gates(working_experiment, evidence_items, state=state)
    state = semantic_outcome.state
    gate_results.extend(semantic_outcome.gates)
    summary_notes.extend(semantic_outcome.summary_notes)

    decoy_outcome = evaluate_decoy_survival_gate(
        working_experiment,
        min_decoy_coverage=cfg.tribunal_thresholds.min_decoy_coverage,
        state=state,
    )
    state = decoy_outcome.state
    gate_results.append(decoy_outcome.gate)
    summary_notes.extend(decoy_outcome.summary_notes)

    market_data_outcome = evaluate_market_data_source_policy(
        provenance=execution_report.market_data_provenance,
        requires_shorting=bool(execution_report.requires_shorting),
        policy=cfg.runtime_policy,
        state=state,
    )
    state = market_data_outcome.state
    summary_notes.extend(market_data_outcome.summary_notes)

    robustness_outcome = evaluate_robustness_gate(
        working_experiment,
        evidence_items,
        thresholds=cfg.tribunal_thresholds,
        state=state,
    )
    state = robustness_outcome.state
    gate_results.append(robustness_outcome.gate)
    summary_notes.extend(robustness_outcome.summary_notes)

    working_experiment.state = state
    setattr(working_experiment, "_ledger_evidence_items", evidence_items)
    decision = AdjudicationDecision(
        previous_state=previous_state,
        new_state=state,
        gate_results=gate_results,
        summary_notes=summary_notes,
        runtime_mode=readiness.run_mode,
        config_fingerprint=readiness.config_fingerprint,
        benchmark_report=benchmark_outcome.benchmark_report,
        execution_report=execution_report,
        evaluation_time_utc=working_experiment.evidence_bundle.evaluation_time_utc,
        market_data_subject_id=working_experiment.evidence_bundle.market_data_subject_id,
    )
    working_experiment.promotion_history.append(decision)

    if commit:
        commit_state_transition(working_experiment, issue_write_authority(), created_at=created_at)
    experiment.state = working_experiment.state
    experiment.evidence_bundle = working_experiment.evidence_bundle
    experiment.promotion_history = list(working_experiment.promotion_history)
    return state


__all__ = ["adjudicate", "_evaluate_execution_realism", "_evaluate_snapshot_freshness"]
