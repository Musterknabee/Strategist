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

from strategy_validator.contracts.oracle_strategic_memory import OracleResearchPriorityReport
def build_oracle_research_priority_report(payload: Any, fusion_report: Any|None=None, posterior_report: Any|None=None, thesis_memory_report: Any|None=None, strategic_memory_horizon_report: Any|None=None, now_utc: datetime|None=None, **_: Any)->OracleResearchPriorityReport:
    t=now_utc or _now()
    return OracleResearchPriorityReport(generated_at_utc=t,universe_label=_universe(payload),oracle_run_id=_run(payload,t),input_timestamp_utc=_ts(payload,t),dominant_regime=_regime(fusion_report),strategic_posture=_posture(fusion_report),history_integrity_status="CURRENT_ONLY",sealed_history_observation_count=0,unsealed_history_excluded_count=0,exact_evidence_support_score=_score(fusion_report,posterior_report,thesis_memory_report,strategic_memory_horizon_report),summary_line="Research priorities generated from current advisory inputs.",highest_priority_id=None,items=[],operator_actions=["Review priority queue before execution."])
def load_research_priority_report(path: str|Path)->OracleResearchPriorityReport: return OracleResearchPriorityReport.model_validate(_read(path))
def render_oracle_research_priority_markdown(report: OracleResearchPriorityReport)->str: return _md("Oracle Research Priority Report", report)
__all__=["build_oracle_research_priority_report","load_research_priority_report","render_oracle_research_priority_markdown"]
