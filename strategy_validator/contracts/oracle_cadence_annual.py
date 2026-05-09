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

class OracleAnnualReviewReport(BaseModel):
    schema_version: Literal["oracle_annual_review_report/v1"] = "oracle_annual_review_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_semiannual_audit_id: str | None = None
    latest_semiannual_audit_classification: OracleSemiannualAuditClassification | None = None
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    semiannual_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_semiannual_audit_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleAnnualReviewEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_annual_review_evidence_manifest/v1"] = "oracle_annual_review_evidence_manifest/v1"
    generated_at_utc: datetime
    annual_review_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_semiannual_lane_path: str
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_semiannual_audit_id: str | None = None
    latest_semiannual_audit_classification: OracleSemiannualAuditClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleAnnualReviewEvidenceVerification(BaseModel):
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

class OracleAnnualLaneEntry(BaseModel):
    schema_version: Literal["oracle_annual_lane_entry/v1"] = "oracle_annual_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    annual_review_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    annual_review_classification: OracleAnnualReviewClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_semiannual_audit_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}

__all__ = (
    "OracleAnnualReviewReport",
    "OracleAnnualReviewEvidenceManifest",
    "OracleAnnualReviewEvidenceVerification",
    "OracleAnnualLaneEntry",
)
