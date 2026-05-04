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


class OracleMonthlyDigestReport(BaseModel):
    schema_version: Literal["oracle_monthly_digest_report/v1"] = "oracle_monthly_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    latest_current_doctrine_posture: OracleMemoryReviewClassification | None = None
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    drift_classification_counts: dict[str, int] = Field(default_factory=dict)
    recurring_patterns: List[str] = Field(default_factory=list)
    observed_drift_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMonthlyDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_monthly_digest_evidence_manifest/v1"] = "oracle_monthly_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    monthly_digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_doctrine_lane_path: str
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    latest_current_doctrine_posture: OracleMemoryReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleMonthlyDigestEvidenceVerification(BaseModel):
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


class OracleMonthlyLaneEntry(BaseModel):
    schema_version: Literal["oracle_monthly_lane_entry/v1"] = "oracle_monthly_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    monthly_digest_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    doctrine_memory_classification: OracleDoctrineMemoryClassification
    latest_drift_classification: OracleDoctrineDriftClassification | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


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


class OracleSemiannualAuditReport(BaseModel):
    schema_version: Literal["oracle_semiannual_audit_report/v1"] = "oracle_semiannual_audit_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_quarterly_review_id: str | None = None
    latest_quarterly_review_classification: OracleQuarterlyReviewClassification | None = None
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    quarterly_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_quarterly_review_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleSemiannualAuditEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_semiannual_audit_evidence_manifest/v1"] = "oracle_semiannual_audit_evidence_manifest/v1"
    generated_at_utc: datetime
    semiannual_audit_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_quarterly_lane_path: str
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_quarterly_review_id: str | None = None
    latest_quarterly_review_classification: OracleQuarterlyReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleSemiannualAuditEvidenceVerification(BaseModel):
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


class OracleSemiannualLaneEntry(BaseModel):
    schema_version: Literal["oracle_semiannual_lane_entry/v1"] = "oracle_semiannual_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    semiannual_audit_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    semiannual_audit_classification: OracleSemiannualAuditClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_quarterly_review_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


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


class OracleConstitutionalDigestReport(BaseModel):
    schema_version: Literal["oracle_constitutional_digest_report/v1"] = "oracle_constitutional_digest_report/v1"
    generated_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    latest_annual_review_id: str | None = None
    latest_annual_review_classification: OracleAnnualReviewClassification | None = None
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    annual_classification_counts: dict[str, int] = Field(default_factory=dict)
    observed_annual_review_ids: List[str] = Field(default_factory=list)
    recurring_patterns: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalDigestEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_constitutional_digest_evidence_manifest/v1"] = "oracle_constitutional_digest_evidence_manifest/v1"
    generated_at_utc: datetime
    constitutional_digest_id: str
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    source_annual_lane_path: str
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    window_entry_count: int = Field(ge=0)
    window_end_sequence_number: int | None = None
    latest_annual_review_id: str | None = None
    latest_annual_review_classification: OracleAnnualReviewClassification | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalDigestEvidenceVerification(BaseModel):
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


class OracleConstitutionalLaneEntry(BaseModel):
    schema_version: Literal["oracle_constitutional_lane_entry/v1"] = "oracle_constitutional_lane_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    sequence_number: int = Field(ge=0)
    entry_id: str
    constitutional_digest_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    constitutional_digest_classification: OracleConstitutionalDigestClassification
    strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] = "NO_STRATEGIC_STACK_HISTORY"
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    latest_annual_review_id: str | None = None
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineLineageIndex(BaseModel):
    schema_version: Literal["oracle_doctrine_lineage_index/v1"] = "oracle_doctrine_lineage_index/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    preferred_strategic_stack_evidence_count: int | None = Field(default=None, ge=0)
    preferred_strategic_stack_requirement_met: bool | None = None
    closure_snapshot_paths: List[str] = Field(default_factory=list)
    governed_exception_paths: List[str] = Field(default_factory=list)
    oracle_evidence_manifest_paths: List[str] = Field(default_factory=list)
    oracle_transition_evidence_paths: List[str] = Field(default_factory=list)
    oracle_memory_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_weekly_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_doctrine_drift_evidence_paths: List[str] = Field(default_factory=list)
    oracle_monthly_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_quarterly_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_semiannual_audit_evidence_paths: List[str] = Field(default_factory=list)
    oracle_annual_review_evidence_paths: List[str] = Field(default_factory=list)
    oracle_constitutional_digest_evidence_paths: List[str] = Field(default_factory=list)
    oracle_strategic_stack_evidence_paths: List[str] = Field(default_factory=list)
    annual_lane_paths: List[str] = Field(default_factory=list)
    constitutional_lane_paths: List[str] = Field(default_factory=list)
    integrity_warnings: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDoctrineLineageVerification(BaseModel):
    schema_version: Literal["oracle_doctrine_lineage_verification/v1"] = "oracle_doctrine_lineage_verification/v1"
    verified_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    seal_status: OracleDoctrineLineageSealStatus
    completeness_score: float = Field(ge=0.0, le=1.0)
    completeness_percent: int = Field(ge=0, le=100)
    required_layer_count: int = Field(ge=0)
    valid_required_layer_count: int = Field(ge=0)
    layer_presence: dict[str, bool] = Field(default_factory=dict)
    layer_validity: dict[str, bool] = Field(default_factory=dict)
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_layer_valid: bool = False
    strategic_stack_requirement_met: bool = False
    missing_required_layers: List[str] = Field(default_factory=list)
    missing_optional_layers: List[str] = Field(default_factory=list)
    parse_failures: List[str] = Field(default_factory=list)
    integrity_warnings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleConstitutionalGateReport(BaseModel):
    schema_version: Literal["oracle_constitutional_gate_report/v1"] = "oracle_constitutional_gate_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    preferred_strategic_backing_source: str | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    manifest_path: str
    minimum_required_seal_status: OracleDoctrineLineageSealStatus
    lineage_seal_status: OracleDoctrineLineageSealStatus
    lineage_completeness_percent: int = Field(ge=0, le=100)
    constitutional_digest_classification: OracleConstitutionalDigestClassification | None = None
    manifest_verification_status: OracleEvidenceStatus
    strategic_stack_evidence_count: int = Field(default=0, ge=0)
    strategic_stack_requirement_met: bool = False
    trust_status: OracleConstitutionalTrustStatus
    trusted_for_constitutional_use: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    facts: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


