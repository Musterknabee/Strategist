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

class OracleQuarterlyReviewReport(BaseModel):
    schema_version: Literal["oracle_quarterly_review_report/v1"] = "oracle_quarterly_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_monthly_digest_id: str | None = None
    latest_doctrine_memory_classification: OracleDoctrineMemoryClassification | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    quarterly_review_classification: OracleQuarterlyReviewClassification
    monthly_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_monthly_digest_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleQuarterlyReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_quarterly_review_evidence_manifest/v1"] = "oracle_quarterly_review_evidence_manifest/v1"
    generated_at_utc: datetime
    quarterly_review_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_monthly_lane_path: str
    quarterly_review_classification: OracleQuarterlyReviewClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_monthly_digest_id: str | None = None
    latest_doctrine_memory_classification: OracleDoctrineMemoryClassification | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleQuarterlyReviewEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    verified_subject_count: int = Field(ge=0)
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}

class OracleQuarterlyLaneEntry(BaseModel):
    schema_version: Literal["oracle_quarterly_lane_entry/v1"] = "oracle_quarterly_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    quarterly_review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    quarterly_review_classification: OracleQuarterlyReviewClassification
    latest_monthly_digest_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}

__all__ = (
    "OracleQuarterlyReviewReport",
    "OracleQuarterlyReviewEvidenceManifest",
    "OracleQuarterlyReviewEvidenceVerification",
    "OracleQuarterlyLaneEntry",
)
