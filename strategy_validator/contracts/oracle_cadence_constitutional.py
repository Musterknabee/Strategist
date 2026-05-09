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

__all__ = (
    "OracleConstitutionalDigestReport",
    "OracleConstitutionalDigestEvidenceManifest",
    "OracleConstitutionalDigestEvidenceVerification",
    "OracleConstitutionalLaneEntry",
    "OracleDoctrineLineageIndex",
    "OracleDoctrineLineageVerification",
    "OracleConstitutionalGateReport",
)
