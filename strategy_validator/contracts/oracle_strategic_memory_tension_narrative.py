from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import OracleStrategicPosture


class OracleStrategicTensionItem(BaseModel):
    tension_id: str
    tension_kind: Literal["POSTURE_CONSENSUS", "OPPORTUNITY_CONSENSUS", "POSTURE_VS_RISK_STACK", "LEAD_COHORT_FRAGILITY", "GRAPH_CASCADE_VS_POSTURE", "RESEARCH_PRIORITY_VS_POSTURE", "EXECUTION_OUTCOME_FEEDBACK"]
    alignment_state: Literal["CONSENSUS", "TENSION", "SEVERE_TENSION"]
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    severity_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    resolution_guidance: str

    model_config = {"extra": "forbid"}

class OracleStrategicTensionReport(BaseModel):
    schema_version: Literal["oracle_strategic_tension_report/v1"] = "oracle_strategic_tension_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    consensus_strength_score: float = Field(ge=0.0, le=1.0)
    highest_severity_tension_id: str | None = None
    tension_item_ids: List[str] = Field(default_factory=list)
    consensus_item_ids: List[str] = Field(default_factory=list)
    items: List[OracleStrategicTensionItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class OracleStrategicNarrativeItem(BaseModel):
    narrative_id: str
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    driver_kind: Literal["REGIME_DRIVER", "STRATEGY_DRIVER", "DOCTRINE_DRIVER", "SCENARIO_DRIVER", "CONTRADICTION_DRIVER", "INVESTIGATION_DRIVER"]
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    rank_score: float = Field(ge=0.0, le=1.0)
    title: str
    summary_line: str
    evidence: List[str] = Field(default_factory=list)
    related_strategy_ids: List[str] = Field(default_factory=list)
    trust_bias: Literal["TRUST_MORE", "HOLD", "TRUST_LESS"] = "HOLD"
    operator_guidance: str

    model_config = {"extra": "forbid"}

class OracleStrategicNarrativeReport(BaseModel):
    schema_version: Literal["oracle_strategic_narrative_report/v1"] = "oracle_strategic_narrative_report/v1"
    generated_at_utc: datetime
    universe_label: str
    oracle_run_id: str
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    strategic_posture: OracleStrategicPosture
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    conviction_state: Literal["HIGH_CONVICTION", "GUARDED_CONVICTION", "FRAGILE_CONVICTION", "BROKEN_CONVICTION"]
    conviction_score: float = Field(ge=0.0, le=1.0)
    fragility_score: float = Field(ge=0.0, le=1.0)
    summary_line: str
    highest_ranked_narrative_id: str | None = None
    items: List[OracleStrategicNarrativeItem] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = ['OracleStrategicTensionItem', 'OracleStrategicTensionReport', 'OracleStrategicNarrativeItem', 'OracleStrategicNarrativeReport']
