from __future__ import annotations
from typing import Any
from strategy_validator.contracts.kernel_reports import KernelDecisionReport

def _dump(v: Any):
    if hasattr(v,"model_dump"): return v.model_dump(mode="json")
    return v if isinstance(v,dict) else repr(v)
def build_kernel_decision_report(*, experiment_id: str, strategy_id: str, decision: Any)->KernelDecisionReport:
    ns=getattr(decision,"new_state",None); ps=getattr(decision,"previous_state",None); dt=getattr(decision,"decided_at",None)
    gate_results=[_dump(g) for g in getattr(decision,"gate_results",[])]
    gate_failures=[
        str(item.get("reason") or item.get("gate_name"))
        for item in gate_results
        if isinstance(item,dict) and not item.get("passed",False)
    ]
    execution_report=getattr(decision,"execution_report",None)
    benchmark_report=getattr(decision,"benchmark_report",None)
    return KernelDecisionReport(
        report_id=f"kernel:{experiment_id}:{getattr(dt,'isoformat',lambda: 'na')()}",
        experiment_id=experiment_id,
        strategy_id=strategy_id,
        generated_at_utc=dt,
        promotion_state=getattr(ns,"name",str(ns)),
        gate_failures=gate_failures,
        gate_results=gate_results,
        benchmark_summary=_dump(benchmark_report) if benchmark_report is not None else {},
        execution_realism_summary=_dump(execution_report) if execution_report is not None else {},
        summary_notes=list(getattr(decision,"summary_notes",[]) or []),
    )
__all__=["build_kernel_decision_report"]
