from __future__ import annotations

from strategy_validator.contracts.decision_record import DecisionRecord


def translate_decision_record_to_governance(record: DecisionRecord) -> dict[str, str | int]:
    has_blockers = bool(record.blocking_reasons)
    failed_gates = sum(1 for gate in record.gate_results if not gate.passed)
    if has_blockers or failed_gates:
        priority = 'CRITICAL_PRIORITY' if failed_gates > 1 else 'ELEVATED_PRIORITY'
        routing = 'CONSTITUTIONAL_REPAIR_QUEUE' if has_blockers else 'HEIGHTENED_REVIEW_QUEUE'
    else:
        priority = 'ROUTINE_PRIORITY'
        routing = 'ROUTINE_REVIEW_QUEUE'
    return {
        'strategy_id': record.strategy_id,
        'experiment_id': record.experiment_id,
        'priority_band': priority,
        'review_target': routing,
        'blocking_reason_count': len(record.blocking_reasons),
        'failed_gate_count': failed_gates,
        'promotion_state': record.promotion_state,
    }
