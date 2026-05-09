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

class OracleDoctrineDriftReport(BaseModel):
    schema_version: Literal["oracle_doctrine_drift_report/v1"] = "oracle_doctrine_drift_report/v1"
    generated_at_utc: datetime
    previous_digest_id: str
    current_digest_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_verification_status: OracleEvidenceStatus
    current_verification_status: OracleEvidenceStatus
    comparison_status: OracleEvidenceStatus
    previous_doctrine_posture: OracleMemoryReviewClassification
    current_doctrine_posture: OracleMemoryReviewClassification
    previous_latest_review_classification: OracleMemoryReviewClassification | None = None
    current_latest_review_classification: OracleMemoryReviewClassification | None = None
    previous_latest_global_action: GlobalAdvisoryAction | None = None
    current_latest_global_action: GlobalAdvisoryAction | None = None
    previous_latest_epistemic_status: EpistemicStatus | None = None
    current_latest_epistemic_status: EpistemicStatus | None = None
    recurring_pattern_overlap_count: int = Field(ge=0)
    recurring_pattern_shift_count: int = Field(ge=0)
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleDoctrineDriftEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_doctrine_drift_evidence_manifest/v1"] = "oracle_doctrine_drift_evidence_manifest/v1"
    generated_at_utc: datetime
    drift_id: str
    lane_id: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_previous_digest_path: str
    source_current_digest_path: str
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    previous_doctrine_posture: OracleMemoryReviewClassification
    current_doctrine_posture: OracleMemoryReviewClassification
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

class OracleDoctrineDriftEvidenceVerification(BaseModel):
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

class OracleDoctrineLaneEntry(BaseModel):
    schema_version: Literal["oracle_doctrine_lane_entry/v1"] = "oracle_doctrine_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    drift_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    drift_classification: OracleDoctrineDriftClassification
    drift_level: OracleDriftLevel
    current_doctrine_posture: OracleMemoryReviewClassification
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}

__all__ = (
    "OracleDoctrineDriftReport",
    "OracleDoctrineDriftEvidenceManifest",
    "OracleDoctrineDriftEvidenceVerification",
    "OracleDoctrineLaneEntry",
)
