from __future__ import annotations
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

def _now(): return datetime.now(timezone.utc)
def _read(path): 
    with Path(path).open("r",encoding="utf-8") as h:
        data=json.load(h)
    if not isinstance(data,dict): raise ValueError("expected JSON object")
    return data
def _universe(payload): return str(getattr(payload,"universe_label","unknown"))
def _ts(payload, fallback): return getattr(payload,"generated_for_utc",fallback) or fallback
def _run(payload, t): return f"oracle:{_universe(payload).replace(' ','_')}:{t.isoformat()}"
def _regime(fusion): return str(getattr(fusion,"dominant_regime","NEUTRAL_REGIME"))
def _posture(fusion): return str(getattr(fusion,"strategic_posture","BALANCED_OBSERVATION"))
def _score(*xs):
    vals=[]
    for x in xs:
        v=getattr(x,"exact_evidence_support_score",None)
        if v is not None:
            try: vals.append(float(v))
            except Exception: pass
    return round(sum(vals)/len(vals),6) if vals else 0.0
def _md(title, report): return f"# {title}\n\n- schema_version: {getattr(report,'schema_version','')}\n- universe_label: {getattr(report,'universe_label','unknown')}\n- summary: {getattr(report,'summary_line','')}\n"

from strategy_validator.contracts.oracle_strategic_memory import OracleInvestigationOutcomeInput, OracleResearchExecutionMemoryReport, OracleResearchPriorityReport
def load_investigation_outcome_input(path: str|Path)->OracleInvestigationOutcomeInput: return OracleInvestigationOutcomeInput.model_validate(_read(path))
def build_oracle_research_execution_memory_report(priority_report: OracleResearchPriorityReport, outcome_input: OracleInvestigationOutcomeInput|None=None, now_utc: datetime|None=None, **_: Any)->OracleResearchExecutionMemoryReport:
    t=now_utc or _now(); completed=[]; deferred=[]; escalated=[]
    for item in getattr(outcome_input,"items",[]) if outcome_input is not None else []:
        pid=getattr(item,"priority_id",""); state=getattr(item,"execution_state",""); disp=getattr(item,"outcome_disposition","")
        if state=="COMPLETED": completed.append(pid)
        if state in {"DEFERRED","ABORTED"}: deferred.append(pid)
        if disp=="ESCALATED": escalated.append(pid)
    return OracleResearchExecutionMemoryReport(generated_at_utc=t,universe_label=priority_report.universe_label,oracle_run_id=priority_report.oracle_run_id,input_timestamp_utc=priority_report.input_timestamp_utc,preferred_strategic_backing_source=getattr(priority_report,"preferred_strategic_backing_source",None),preferred_strategic_backing_classification=getattr(priority_report,"preferred_strategic_backing_classification",None),exact_evidence_support_score=getattr(priority_report,"exact_evidence_support_score",0.0),summary_line="Research execution memory summarized from priorities and optional outcomes.",completed_priority_ids=sorted(set(completed)),deferred_priority_ids=sorted(set(deferred)),escalated_priority_ids=sorted(set(escalated)),items=[],operator_actions=["Advisory-only; no ledger mutation authority."])
def load_research_execution_memory_report(path: str|Path)->OracleResearchExecutionMemoryReport: return OracleResearchExecutionMemoryReport.model_validate(_read(path))
def render_oracle_research_execution_memory_markdown(report: OracleResearchExecutionMemoryReport)->str: return _md("Oracle Research Execution Memory Report", report)
__all__=["build_oracle_research_execution_memory_report","load_investigation_outcome_input","load_research_execution_memory_report","render_oracle_research_execution_memory_markdown"]
