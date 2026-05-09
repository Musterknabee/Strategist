from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.operational import EvidenceResourceDescriptor
from strategy_validator.contracts.oracle_types import (
    AdvisoryRegime,
    EpistemicStatus,
    GlobalAdvisoryAction,
    OracleAnnualReviewClassification,
    OracleConstitutionalDigestClassification,
    OracleConstitutionalTrustStatus,
    OracleDoctrineDriftClassification,
    OracleDoctrineLineageSealStatus,
    OracleDoctrineMemoryClassification,
    OracleDriftLevel,
    OracleEvidenceStatus,
    OracleMemoryReviewClassification,
    OracleQuarterlyReviewClassification,
    OracleSemiannualAuditClassification,
    OracleTransitionClassification,
)

class OracleMemoryLaneEntry(BaseModel):
    schema_version: Literal["oracle_memory_lane_entry/v1"] = "oracle_memory_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    transition_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    transition_classification: OracleTransitionClassification
    drift_score: float = Field(ge=0.0, le=1.0)
    current_input_timestamp_utc: datetime
    current_epistemic_status: EpistemicStatus
    current_recommended_global_action: GlobalAdvisoryAction
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleMemoryLaneSummary(BaseModel):
    schema_version: Literal["oracle_memory_lane_summary/v1"] = "oracle_memory_lane_summary/v1"
    generated_at_utc: datetime
    lane_id: str
    entry_count: int = Field(ge=0)
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_transition_classification: OracleTransitionClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    severe_drift_count: int = Field(ge=0)
    evidence_gap_count: int = Field(ge=0)
    classification_counts: dict[str, int] = Field(default_factory=dict)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleMemoryReviewReport(BaseModel):
    schema_version: Literal["oracle_memory_review_report/v1"] = "oracle_memory_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_transition_classification: OracleTransitionClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    review_classification: OracleMemoryReviewClassification
    evidence_gap_count: int = Field(ge=0)
    epistemic_escalation_count: int = Field(ge=0)
    global_action_escalation_count: int = Field(ge=0)
    severe_or_material_drift_count: int = Field(ge=0)
    strategy_retrain_candidate_ids: List[str] = Field(default_factory=list)
    observed_transition_ids: List[str] = Field(default_factory=list)
    triggers: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleMemoryReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_memory_review_evidence_manifest/v1"] = "oracle_memory_review_evidence_manifest/v1"
    generated_at_utc: datetime
    review_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_memory_lane_path: str
    review_classification: OracleMemoryReviewClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleMemoryReviewEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class OracleReviewLaneEntry(BaseModel):
    schema_version: Literal["oracle_review_lane_entry/v1"] = "oracle_review_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    review_classification: OracleMemoryReviewClassification
    window_end_sequence_number: int | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}

__all__ = (
    "OracleMemoryLaneEntry",
    "OracleMemoryLaneSummary",
    "OracleMemoryReviewReport",
    "OracleMemoryReviewEvidenceManifest",
    "OracleMemoryReviewEvidenceVerification",
    "OracleReviewLaneEntry",
)
