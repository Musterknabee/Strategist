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

from strategy_validator.contracts.oracle_strategic_fusion import StrategyHealthPosteriorReport
def build_strategy_health_posterior_report(payload: Any, fusion_report: Any|None=None, now_utc: datetime|None=None, **_: Any)->StrategyHealthPosteriorReport:
    t=now_utc or _now(); vals=[]
    for s in getattr(payload,"strategies",[]) or []:
        v=getattr(s,"posterior_edge_confidence",None)
        if v is not None:
            try: vals.append(float(v))
            except Exception: pass
    avg=round(sum(vals)/len(vals),6) if vals else 0.0
    return StrategyHealthPosteriorReport(generated_at_utc=t,universe_label=_universe(payload),oracle_run_id=getattr(fusion_report,"oracle_run_id",_run(payload,t)),input_timestamp_utc=_ts(payload,t),dominant_regime=_regime(fusion_report),strategic_posture=_posture(fusion_report),preferred_strategic_backing_source=getattr(fusion_report,"preferred_strategic_backing_source",None),preferred_strategic_backing_classification=getattr(fusion_report,"preferred_strategic_backing_classification",None),exact_evidence_support_score=_score(fusion_report),average_posterior_edge_confidence=avg,degraded_strategy_ids=[],recovering_strategy_ids=[],operator_actions=["Review posterior health before promotion."],strategies=[],summary_line=f"Posterior health summarized for {len(vals)} strategy snapshot(s).")
def render_strategy_health_posterior_markdown(report: StrategyHealthPosteriorReport)->str: return _md("Strategy Health Posterior Report", report)
__all__=["build_strategy_health_posterior_report","render_strategy_health_posterior_markdown"]
