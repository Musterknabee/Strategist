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

from strategy_validator.contracts.oracle_strategic_programs import OracleStrategyCohortReport
def build_oracle_strategy_cohort_report(payload: Any, fusion_report: Any|None=None, posterior_report: Any|None=None, thesis_memory_report: Any|None=None, transition_report: Any|None=None, now_utc: datetime|None=None, **_: Any)->OracleStrategyCohortReport:
    t=now_utc or _now()
    return OracleStrategyCohortReport(generated_at_utc=t,universe_label=_universe(payload),oracle_run_id=getattr(fusion_report,"oracle_run_id",_run(payload,t)),input_timestamp_utc=_ts(payload,t),dominant_regime=_regime(fusion_report),strategic_posture=_posture(fusion_report),preferred_strategic_backing_source=getattr(fusion_report,"preferred_strategic_backing_source",None),preferred_strategic_backing_classification=getattr(fusion_report,"preferred_strategic_backing_classification",None),exact_evidence_support_score=_score(fusion_report,posterior_report,thesis_memory_report),transition_classification=getattr(transition_report,"transition_classification",None),summary_line="Strategy cohort initialized from advisory context.",lead_strategy_ids=[],pressured_strategy_ids=[],items=[],operator_actions=["Cohort ranking is advisory, not promotion authority."])
def load_strategy_cohort_report(path: str|Path)->OracleStrategyCohortReport: return OracleStrategyCohortReport.model_validate(_read(path))
def render_oracle_strategy_cohort_markdown(report: OracleStrategyCohortReport)->str: return _md("Oracle Strategy Cohort Report", report)
__all__=["build_oracle_strategy_cohort_report","load_strategy_cohort_report","render_oracle_strategy_cohort_markdown"]
