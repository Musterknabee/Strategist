from __future__ import annotations

from typing import Any

from strategy_validator.validator.services.decision_service import adjudicate_experiment
from strategy_validator.validator.services.promotion_commit_service import build_kernel_decision_report
from strategy_validator.contracts.operator_reports import OperatorGovernanceReport
from strategy_validator.application.translators import translate_decision_record_to_governance


def run_oracle_adjudication(*args: Any, **kwargs: Any):
    """Transport-neutral façade over the canonical adjudication entrypoint."""
    return adjudicate_experiment(*args, **kwargs)


__all__ = ['run_oracle_adjudication']


from strategy_validator.contracts.decision_record import DecisionRecord


def build_decision_record(*, experiment_id: str, strategy_id: str, decision) -> DecisionRecord:
    blocking_reasons = [gate.reason for gate in getattr(decision, 'gate_results', []) if not gate.passed and gate.reason]
    benchmark_summary = {}
    benchmark_report = getattr(decision, 'benchmark_report', None)
    if benchmark_report is not None:
        benchmark_summary = benchmark_report.model_dump(mode='json') if hasattr(benchmark_report, 'model_dump') else dict(benchmark_report) if isinstance(benchmark_report, dict) else {'repr': repr(benchmark_report)}
    execution_summary = {}
    execution_report = getattr(decision, 'execution_report', None)
    if execution_report is not None:
        execution_summary = execution_report.model_dump(mode='json') if hasattr(execution_report, 'model_dump') else dict(execution_report) if isinstance(execution_report, dict) else {'repr': repr(execution_report)}
    return DecisionRecord(
        record_id=f"decision:{experiment_id}:{getattr(decision, 'decided_at').isoformat()}",
        strategy_id=strategy_id,
        experiment_id=experiment_id,
        decision_class=getattr(decision, 'new_state').name if hasattr(getattr(decision, 'new_state'), 'name') else str(getattr(decision, 'new_state')),
        promotion_state=getattr(decision, 'new_state').name if hasattr(getattr(decision, 'new_state'), 'name') else str(getattr(decision, 'new_state')),
        blocking_reasons=[item for item in blocking_reasons if item],
        summary_notes=list(getattr(decision, 'summary_notes', [])),
        gate_results=list(getattr(decision, 'gate_results', [])),
        benchmark_summary=benchmark_summary,
        execution_realism_summary=execution_summary,
        source_decision=decision if hasattr(decision, 'model_dump') else None,
    )


def build_kernel_report(*, experiment_id: str, strategy_id: str, decision):
    return build_kernel_decision_report(experiment_id=experiment_id, strategy_id=strategy_id, decision=decision)


def build_operator_governance_report(*, decision_record):
    payload = translate_decision_record_to_governance(decision_record)
    priority_band = str(payload['priority_band'])
    queue_priority = 90 if priority_band == 'CRITICAL_PRIORITY' else 60 if priority_band == 'ELEVATED_PRIORITY' else 20
    escalation_posture = 'CRITICAL' if priority_band == 'CRITICAL_PRIORITY' else 'ELEVATED' if priority_band == 'ELEVATED_PRIORITY' else 'NORMAL'
    routing_class = str(payload['review_target'])
    return OperatorGovernanceReport(
        report_id=f"operator:{decision_record.record_id}",
        decision_record_id=decision_record.record_id,
        queue_priority=queue_priority,
        escalation_posture=escalation_posture,
        routing_class=routing_class,
        operator_summary=f"Queue priority {queue_priority} with {escalation_posture} posture.",
        blocking_reasons=list(decision_record.blocking_reasons),
    )
