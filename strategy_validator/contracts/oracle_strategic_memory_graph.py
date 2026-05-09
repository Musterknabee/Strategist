from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import AdvisoryRegime
from strategy_validator.contracts.oracle_strategic_memory_common import OracleStrategicPosture


class OracleThesisGraphNode(BaseModel):
    node_id: str
    node_kind: Literal["THESIS", "DOCTRINE_CLAUSE", "STRATEGY_COHORT", "RESEARCH_PRIORITY", "INVESTIGATION_OUTCOME"]
    label: str
    status: str
    cascade_risk_score: float = Field(ge=0.0, le=1.0)
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    connected_node_ids: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleThesisGraphEdge(BaseModel):
    edge_id: str
    source_node_id: str
    target_node_id: str
    relation_kind: Literal["SUPPORTS", "WEAKENS", "PRESSURES", "RELIEVES", "INVESTIGATES", "PROMOTES", "DEMOTES", "DEPENDS_ON"]
    influence_score: float = Field(ge=0.0, le=1.0)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleThesisGraphReport(BaseModel):
    schema_version: Literal["oracle_thesis_graph_report/v1"] = "oracle_thesis_graph_report/v1"
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
    highest_cascade_risk_node_ids: List[str] = Field(default_factory=list)
    nodes: List[OracleThesisGraphNode] = Field(default_factory=list)
    edges: List[OracleThesisGraphEdge] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


__all__ = ['OracleThesisGraphNode', 'OracleThesisGraphEdge', 'OracleThesisGraphReport']
