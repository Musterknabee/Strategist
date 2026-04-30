from __future__ import annotations

from datetime import datetime
from typing import List, Literal

from pydantic import BaseModel, Field

from strategy_validator.contracts.operational import EvidenceResourceDescriptor
from strategy_validator.contracts.oracle_core import OracleDerivedViewClassification
from strategy_validator.contracts.oracle_types import (
    AdvisoryRegime,
    EpistemicStatus,
    GlobalAdvisoryAction,
    OracleDriftLevel,
    OracleEvidenceStatus,
    OracleTransitionClassification,
    StrategyAdvisoryAction,
)

class OracleEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_evidence_manifest/v1"] = "oracle_evidence_manifest/v1"
    generated_at_utc: datetime
    evidence_id: str
    universe_label: str
    input_timestamp_utc: datetime
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    dominant_regime: AdvisoryRegime
    recommended_global_action: GlobalAdvisoryAction
    epistemic_status: EpistemicStatus
    linked_closure_id: str | None = None
    linked_closure_snapshot_path: str | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEvidenceVerification(BaseModel):
    verified_at_utc: datetime
    manifest_path: str
    status: OracleEvidenceStatus = "UNVERIFIED"
    artifact_digests_verified: bool = False
    signature_verified: bool = False
    linked_closure_present: bool = False
    verified_subject_count: int = 0
    digest_mismatches: List[str] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleRegimeTransition(BaseModel):
    previous_dominant_regime: AdvisoryRegime
    current_dominant_regime: AdvisoryRegime
    previous_dominant_probability: float = Field(ge=0.0, le=1.0)
    current_dominant_probability: float = Field(ge=0.0, le=1.0)
    dominant_changed: bool = False
    drift_level: OracleDriftLevel = "STABLE"
    drivers: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class StrategyAdvisoryTransition(BaseModel):
    strategy_id: str
    strategy_type: str
    previous_action: StrategyAdvisoryAction
    current_action: StrategyAdvisoryAction
    previous_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    current_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    posterior_delta: float
    action_changed: bool = False
    drift_level: OracleDriftLevel = "STABLE"
    reasons: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStateTransitionReport(BaseModel):
    schema_version: Literal["oracle_state_transition_report/v1"] = "oracle_state_transition_report/v1"
    generated_at_utc: datetime
    previous_evidence_id: str
    current_evidence_id: str
    universe_label: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_input_timestamp_utc: datetime
    current_input_timestamp_utc: datetime
    previous_verification_status: OracleEvidenceStatus
    current_verification_status: OracleEvidenceStatus
    comparison_status: OracleEvidenceStatus
    previous_linked_closure_id: str | None = None
    current_linked_closure_id: str | None = None
    previous_recommended_global_action: GlobalAdvisoryAction
    current_recommended_global_action: GlobalAdvisoryAction
    previous_epistemic_status: EpistemicStatus
    current_epistemic_status: EpistemicStatus
    regime_transition: OracleRegimeTransition
    strategy_transitions: List[StrategyAdvisoryTransition] = Field(default_factory=list)
    introduced_strategy_ids: List[str] = Field(default_factory=list)
    removed_strategy_ids: List[str] = Field(default_factory=list)
    transition_classification: OracleTransitionClassification = "STATE_STABLE"
    drift_score: float = Field(ge=0.0, le=1.0)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleTransitionEvidenceManifest(BaseModel):
    schema_version: Literal["oracle_transition_evidence_manifest/v1"] = "oracle_transition_evidence_manifest/v1"
    generated_at_utc: datetime
    transition_id: str
    universe_label: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    previous_evidence_id: str
    current_evidence_id: str
    previous_linked_closure_id: str | None = None
    current_linked_closure_id: str | None = None
    transition_classification: OracleTransitionClassification
    drift_score: float = Field(ge=0.0, le=1.0)
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleTransitionEvidenceVerification(BaseModel):
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



class OracleEventLogQuerySpec(BaseModel):
    schema_version: Literal["oracle_event_log_query_spec/v1"] = "oracle_event_log_query_spec/v1"
    start_input_timestamp_utc: datetime | None = None
    end_input_timestamp_utc: datetime | None = None
    strategy_ids: List[str] = Field(default_factory=list)
    dominant_regimes: List[AdvisoryRegime] = Field(default_factory=list)
    epistemic_statuses: List[EpistemicStatus] = Field(default_factory=list)
    max_entries: int | None = Field(default=None, ge=1)

    model_config = {"extra": "forbid"}


class OracleEventLogEntry(BaseModel):
    schema_version: Literal["oracle_event_log_entry/v1"] = "oracle_event_log_entry/v1"
    appended_at_utc: datetime
    lane_id: str
    sequence_number: int = Field(ge=0)
    entry_id: str
    evidence_id: str
    previous_entry_hash: str | None = None
    entry_hash: str
    manifest_path: str
    manifest_sha256: str
    linked_closure_id: str | None = None
    input_timestamp_utc: datetime
    dominant_regime: AdvisoryRegime
    recommended_global_action: GlobalAdvisoryAction
    epistemic_status: EpistemicStatus
    average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    maintain_count: int = Field(ge=0)
    canary_count: int = Field(ge=0)
    hibernate_count: int = Field(ge=0)
    strategy_ids: List[str] = Field(default_factory=list)
    evidence_status: OracleEvidenceStatus
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDerivedViewReport(BaseModel):
    schema_version: Literal["oracle_derived_view_report/v1"] = "oracle_derived_view_report/v1"
    generated_at_utc: datetime
    lane_id: str
    view_label: str
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    first_input_timestamp_utc: datetime | None = None
    last_input_timestamp_utc: datetime | None = None
    latest_event_id: str | None = None
    latest_dominant_regime: AdvisoryRegime | None = None
    latest_global_action: GlobalAdvisoryAction | None = None
    latest_epistemic_status: EpistemicStatus | None = None
    derived_classification: OracleDerivedViewClassification
    classification_counts: dict[str, int] = Field(default_factory=dict)
    regime_counts: dict[str, int] = Field(default_factory=dict)
    global_action_counts: dict[str, int] = Field(default_factory=dict)
    epistemic_counts: dict[str, int] = Field(default_factory=dict)
    evidence_gap_count: int = Field(ge=0)
    elevated_or_unknown_count: int = Field(ge=0)
    defensive_posture_count: int = Field(ge=0)
    retrain_pressure_count: int = Field(ge=0)
    average_posterior_edge_confidence: float = Field(ge=0.0, le=1.0)
    observed_entry_ids: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleDerivedViewCheckpointMetadata(BaseModel):
    schema_version: Literal["oracle_derived_view_checkpoint_metadata/v1"] = "oracle_derived_view_checkpoint_metadata/v1"
    generated_at_utc: datetime
    lane_id: str
    view_label: str
    window_size: int = Field(ge=1)
    source_event_log_path: str
    query_spec: OracleEventLogQuerySpec = Field(default_factory=OracleEventLogQuerySpec)
    file_size_bytes: int = Field(ge=0)
    file_offset_bytes: int = Field(ge=0)
    last_event_log_sequence_number: int | None = None
    last_event_log_entry_hash: str | None = None
    cached_window_entries: List[OracleEventLogEntry] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEventCheckpointManifest(BaseModel):
    schema_version: Literal["oracle_event_checkpoint_manifest/v1"] = "oracle_event_checkpoint_manifest/v1"
    generated_at_utc: datetime
    checkpoint_id: str
    lane_id: str
    view_label: str
    source_event_log_path: str
    execution_authority: Literal["ADVISORY_ONLY"] = "ADVISORY_ONLY"
    derived_classification: OracleDerivedViewClassification
    window_entry_count: int = Field(ge=0)
    window_start_sequence_number: int | None = None
    window_end_sequence_number: int | None = None
    last_entry_hash: str | None = None
    latest_event_id: str | None = None
    integrity_status: Literal["VERIFIED", "INCOMPLETE"]
    subjects: List[EvidenceResourceDescriptor] = Field(default_factory=list)
    missing_artifact_paths: List[str] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}


class OracleEventCheckpointVerification(BaseModel):
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


