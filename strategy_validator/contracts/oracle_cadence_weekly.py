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

class OracleWeeklyDigestReport(BaseModel):
    schema_version: Literal["oracle_weekly_digest_report/v1"] = "oracle_weekly_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_review_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_review_classification: OracleMemoryReviewClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    doctrine_posture: OracleMemoryReviewClassification
    classification_counts: dict[str, int] = Field(default_factory=dict)
    recurring_patterns: List[str] = Field(default_factory=list)
    observed_review_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleWeeklyDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_weekly_digest_evidence_manifest/v1"] = "oracle_weekly_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_review_lane_path: str
    doctrine_posture: OracleMemoryReviewClassification
    window_review_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_review_classification: OracleMemoryReviewClassification | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleWeeklyDigestEvidenceVerification(BaseModel):
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

__all__ = (
    "OracleWeeklyDigestReport",
    "OracleWeeklyDigestEvidenceManifest",
    "OracleWeeklyDigestEvidenceVerification",
)
