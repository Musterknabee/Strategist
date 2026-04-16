from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from strategy_validator.contracts.evidence import EvidenceBundle
from strategy_validator.contracts.tribunal import TribunalOpinion
from strategy_validator.contracts.benchmarks import BenchmarkResult
from strategy_validator.contracts.execution import ExecutionRealismResult
from strategy_validator.core.enums import PromotionState, RuntimeMode


class GateResult(BaseModel):
    gate_name: str
    passed: bool
    reason: Optional[str] = None
    note: Optional[str] = None
    metric_value: Optional[float] = None
    threshold_value: Optional[float] = None

    model_config = {"extra": "forbid"}


class AdjudicationDecision(BaseModel):
    decided_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    previous_state: PromotionState
    new_state: PromotionState
    gate_results: List[GateResult] = Field(default_factory=list)
    summary_notes: List[str] = Field(default_factory=list)
    config_hash: Optional[str] = None
    
    # Production Provenance Linkage
    runtime_mode: Optional[RuntimeMode] = None
    config_fingerprint: Optional[str] = None

    # Typed Forensic Evidence
    benchmark_report: Optional[BenchmarkResult] = None
    execution_report: Optional[ExecutionRealismResult] = None

    # PIT Evaluation Context
    evaluation_time_utc: Optional[datetime] = None
    """
    The lawful point-in-time timestamp used for all market-data snapshot
    lookups during this adjudication.  Reproducible from stored evidence.
    """
    market_data_subject_id: Optional[str] = None
    """
    The typed identity of the market-data subject used for liquidity and
    borrow snapshot lookups.  No hardcoded placeholder identities.
    """

    model_config = {"extra": "forbid"}


class AdjudicationEvent(BaseModel):
    """
    Immutable forensic seal for a single adjudication.
    Captured at the moment of decision to prevent post-hoc manifest drift.
    """
    event_id: str
    experiment_id: str
    sequence_number: int
    decision: AdjudicationDecision
    evidence_snapshot_hash: str  # Hash of the evidence bundle evaluated
    manifest_reproducibility_hash: str # Reproduction bridge
    
    model_config = {"extra": "forbid", "frozen": True}


class ExperimentManifest(BaseModel):
    experiment_id: str
    strategy_name: str
    version: str
    proposer_id: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    state: PromotionState = PromotionState.INVALID
    evidence_bundle: EvidenceBundle
    tribunal_opinions: List[TribunalOpinion] = Field(default_factory=list)
    promotion_history: List[AdjudicationDecision] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


def compute_config_hash(config_data: dict[str, Any]) -> str:
    """Deterministic hash of the configuration dictionary."""
    canonical = json.dumps(config_data, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

AdjudicationDecision.model_rebuild()
ExperimentManifest.model_rebuild()
