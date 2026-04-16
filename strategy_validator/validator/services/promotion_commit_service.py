from __future__ import annotations

from typing import Any

from strategy_validator.contracts.kernel_reports import KernelDecisionReport
from strategy_validator.validator.services.execution_realism_service import summarize_execution_realism


def build_kernel_decision_report(*, experiment_id: str, strategy_id: str, decision: Any) -> KernelDecisionReport:
    gate_results = []
    for gate in getattr(decision, 'gate_results', []):
        if hasattr(gate, 'model_dump'):
            gate_results.append(gate.model_dump(mode='json'))
        elif isinstance(gate, dict):
            gate_results.append(dict(gate))
        else:
            gate_results.append({'repr': repr(gate)})
    gate_failures = [item.get('reason') for item in gate_results if item.get('passed') is False and item.get('reason')]
    benchmark_report = getattr(decision, 'benchmark_report', None)
    benchmark_summary = benchmark_report.model_dump(mode='json') if hasattr(benchmark_report, 'model_dump') else {}
    return KernelDecisionReport(
        report_id=f'kernel:{experiment_id}:{strategy_id}',
        experiment_id=experiment_id,
        strategy_id=strategy_id,
        promotion_state=getattr(getattr(decision, 'new_state', None), 'name', str(getattr(decision, 'new_state', 'UNKNOWN'))),
        gate_failures=[str(item) for item in gate_failures if item],
        gate_results=gate_results,
        benchmark_summary=benchmark_summary,
        execution_realism_summary=summarize_execution_realism(decision),
        summary_notes=list(getattr(decision, 'summary_notes', [])),
    )
