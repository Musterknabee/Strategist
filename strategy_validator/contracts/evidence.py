from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from strategy_validator.core.enums import EvidenceType, MetricSourceMode
from strategy_validator.contracts.data_spine import DataSpineAuditSeal



class MetricProvenance(BaseModel):
    """Forensic record of metric origin and selection."""
    metric_name: str
    source_mode: MetricSourceMode
    upstream_claim_present: bool
    provided_value: Optional[float] = None
    recomputed_value: Optional[float] = None
    verified_value: Optional[float] = None
    source_of_truth_used: MetricSourceMode
    recomputed_reason: Optional[str] = None
    verification_note: Optional[str] = None

    model_config = {"extra": "forbid"}

class Evidence(BaseModel):
    evidence_id: str
    experiment_id: str
    evidence_type: EvidenceType
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    payload: Dict[str, Any]
    source_module: str
    checksum: str

    model_config = {"extra": "forbid"}


class BenchmarkObservation(BaseModel):
    benchmark_id: str
    benchmark_version: str
    benchmark_delta: float
    benchmark_passed: bool | None = None

    model_config = {"extra": "forbid"}


class ReproducibilityManifest(BaseModel):
    code_hash: str = Field(min_length=8)
    data_snapshot_hash: str = Field(min_length=8)
    universe_hash: str = Field(min_length=8)
    feature_graph_hash: str = Field(min_length=8)
    parameter_manifest_hash: str = Field(min_length=8)
    benchmark_version: str = Field(min_length=1)
    cost_model_version: str = Field(min_length=1)
    calendar_version: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class SpanCitation(BaseModel):
    source_id: str
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    source_checksum: str = Field(min_length=8)

    model_config = {"extra": "forbid"}


class SemanticArtifact(BaseModel):
    artifact_id: str
    model_name: str
    interpretation: str
    confidence: float = Field(ge=0.0, le=1.0)
    trust_state: Literal["UNTRUSTED", "REVIEWED"] = "UNTRUSTED"
    span_citations: List[SpanCitation] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class EvidenceBundle(BaseModel):
    evidence_items: List[Evidence] = Field(default_factory=list)
    reproducibility: ReproducibilityManifest
    benchmark_rung: str = Field(min_length=1)
    search_breadth: int = Field(ge=1)

    # Evaluation Context (PIT identity and time)
    evaluation_time_utc: Optional[datetime] = None
    """
    The lawful point-in-time timestamp for market-data snapshot lookups
    and execution evaluation.  If absent, consumers must degrade to
    PROVISIONAL or use the latest evidence timestamp as fallback.
    """
    market_data_subject_id: Optional[str] = None
    """
    The typed identity of the market-data subject (asset/instrument)
    for liquidity and borrow snapshot lookups.  If absent, consumers
    must not fabricate a subject identity; they must either degrade
    to PROVISIONAL or raise.
    """

    # Robustness Metrics
    cpcv_folds: int | None = Field(default=None, ge=2)
    cpcv_passed: bool | None = None
    cpcv_path_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    cpcv_path_stability: float | None = None
    incrementality_significant: bool | None = None
    incrementality_p_value: float | None = None
    incrementality_coefficient: float | None = None
    dsr_estimate: float | None = None
    pbo_estimate: float | None = None
    
    # Decoy Metrics
    decoy_suite_version: str | None = None
    decoy_survival_passed: bool | None = None
    decoy_coverage: float | None = Field(default=None, ge=0.0, le=1.0)
    
    # Data Spine Forensic Seal
    data_spine_seal: Optional[DataSpineAuditSeal] = None
    
    semantic_artifacts: List[SemanticArtifact] = Field(default_factory=list)
    robustness_provenance: List[MetricProvenance] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
