from __future__ import annotations

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

from strategy_validator.contracts.oracle_types import (
    OracleArtifactCoverageStatus,
    OracleArtifactIntegrityStatus,
    OracleAutomationPosture,
    OracleConstitutionalTrustStatus,
    OracleEscalationLane,
    OracleEvidenceStatus,
    OracleExplanationCategory,
    OracleGovernanceClaimActionSeverity,
    OracleGovernanceClaimCode,
    OracleGovernanceClaimDisposition,
    OracleGovernanceClaimLeaseAction,
    OracleGovernanceClaimLeaseCoverage,
    OracleGovernanceClaimLeaseHealth,
    OracleGovernanceClaimLeaseMode,
    OracleGovernanceClaimLeaseRenewalPosture,
    OracleGovernanceClaimOperability,
    OracleGovernanceClaimProcessPosture,
    OracleGovernanceClaimWorkerLane,
    OracleGovernanceDimension,
    OracleGovernanceDispatchPosture,
    OracleGovernanceDispatchTimeliness,
    OracleGovernanceDispatchClaimUrgency,
    OracleGovernancePlaneStatus,
    OracleGovernancePrimarySeverity,
    OracleGovernancePriorityBand,
    OracleGovernanceReviewTarget,
    OracleOperatorReadiness,
    OraclePropagationPosture,
    OracleReliancePosture,
    OracleSupportChainRemediationStatus,
    OracleSupportVerificationStatus,
)
from strategy_validator.contracts.oracle_evidence_events import OracleEventLogQuerySpec

from strategy_validator.contracts.oracle_core import (
    OracleArtifactFreshnessItem,
    OracleArtifactLineageItem,
    OracleGovernanceActionItem,
    OracleGovernanceClaimActionItem,
    OracleGovernanceCode,
    OracleGovernanceQueueKey,
)

class OracleExplanationNode(BaseModel):
    node_id: str
    parent_node_id: str | None = None
    category: OracleExplanationCategory
    conclusion: str
    detail: str
    facts: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleTrustExplanationReport(BaseModel):
    schema_version: Literal["oracle_trust_explanation_report/v1"] = "oracle_trust_explanation_report/v1"
    generated_at_utc: datetime
    explanation_kind: Literal["derived_view", "event_checkpoint", "lineage_verification", "constitutional_gate"]
    subject_schema_version: str
    subject_path: str | None = None
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    exact_evidence_support_score: float = Field(default=0.0, ge=0.0, le=1.0)
    summary_line: str
    nodes: List[OracleExplanationNode] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleOperatorDiagnosticReport(BaseModel):
    schema_version: Literal["oracle_operator_diagnostic_report/v1"] = "oracle_operator_diagnostic_report/v1"
    generated_at_utc: datetime
    diagnostic_kind: Literal["why_restricted", "why_blocked"]
    subject_path: str | None = None
    trust_status: OracleConstitutionalTrustStatus
    blocked: bool = False
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    summary_line: str
    reasons: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    explanation: OracleTrustExplanationReport | None = None

    model_config = {"extra": "forbid"}


class OracleStatusPackSection(BaseModel):
    section_id: Literal["lineage", "oracle_posture", "constitutional_gate", "closure_attestation", "governed_exception", "temporal_lane"]
    status: str
    summary_line: str
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    facts: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    explanation: OracleTrustExplanationReport | None = None

    model_config = {"extra": "forbid"}


class OracleOperatorWorkboardItemReport(BaseModel):
    work_item_key: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    action_owner_lane: str
    claim_operability: str
    dispatch_posture: str
    urgency: str
    score: int
    summary_line: str
    recommended_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleOperatorWorkboardReport(BaseModel):
    schema_version: Literal["oracle_operator_workboard/v1"] = "oracle_operator_workboard/v1"
    board_label: str
    queue_key: str
    review_target: str
    priority_band: str
    review_due_by_utc: datetime
    review_sort_key: str
    work_item_count: int = Field(ge=0)
    summary_line: str
    queue_summary_line: str
    recommended_next_actions: List[str] = Field(default_factory=list)
    entries: List[OracleOperatorWorkboardItemReport] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleStatusPackReport(BaseModel):
    schema_version: Literal["oracle_status_pack_report/v1"] = "oracle_status_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    active_governed_exception_ids: List[str] = Field(default_factory=list)
    summary_line: str
    operator_actions: List[str] = Field(default_factory=list)
    sections: List[OracleStatusPackSection] = Field(default_factory=list)
    operator_workboard: OracleOperatorWorkboardReport | None = None
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleIncidentPackArtifact(BaseModel):
    artifact_kind: str
    source_path: str
    sha256: str
    pack_path: str | None = None
    summary_line: str = ""
    required: bool = False

    model_config = {"extra": "forbid"}


class OracleIncidentPackReport(BaseModel):
    schema_version: Literal["oracle_incident_pack_report/v1"] = "oracle_incident_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    trust_status: OracleConstitutionalTrustStatus
    incident_kind: Literal["restricted", "untrusted", "blocked", "trusted_context"]
    blocked: bool = False
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    summary_line: str
    recommended_next_actions: List[str] = Field(default_factory=list)
    primary_diagnostic: OracleOperatorDiagnosticReport | None = None
    status_pack: OracleStatusPackReport
    artifacts: List[OracleIncidentPackArtifact] = Field(default_factory=list)
    operator_workboard: OracleOperatorWorkboardReport | None = None
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleCompactedStateRebuildReport(BaseModel):
    schema_version: Literal["oracle_compacted_state_rebuild_report/v1"] = "oracle_compacted_state_rebuild_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    source_event_log_path: str
    view_label: str
    previous_replay_status: Literal["CURRENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"] | None = None
    previous_metadata_found: bool = False
    rebuilt_window_entry_count: int = Field(ge=0)
    rebuilt_entry_ids: List[str] = Field(default_factory=list)
    rebuilt_file_offset_bytes: int = Field(ge=0)
    rebuilt_last_event_log_sequence_number: int | None = None
    rebuilt_last_event_log_entry_hash: str | None = None
    compacted_window_digest_sha256: str = ""
    summary_line: str
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleBriefingSection(BaseModel):
    section_id: Literal["trust_banner", "regime_state", "strategy_health", "strategic_posture", "strategic_narrative", "belief_drift_timeline", "opportunity_queue", "strategy_cohorts", "thesis_evolution", "thesis_graph", "strategic_tensions", "contradiction_resolution", "intervention_simulation", "strategic_campaigns", "campaign_execution", "scenario_lab", "doctrine_adaptation", "research_priorities", "investigation_outcomes", "doctrine_posture", "closure_posture", "operator_queue", "open_risks", "active_exceptions"]
    title: str
    status: str
    summary_line: str
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    facts: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    provenance_refs: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleBriefingPackReport(BaseModel):
    schema_version: Literal["oracle_briefing_pack_report/v1"] = "oracle_briefing_pack_report/v1"
    generated_at_utc: datetime
    repo_root: str
    search_root: str
    oracle_policy_version: str = "oracle-default-v1"
    oracle_policy_sha256: str = ""
    oracle_policy_path: str | None = None
    operator_readiness: OracleOperatorReadiness = "REVIEW_WITH_CAUTION"
    operator_readiness_summary_line: str = ""
    operator_readiness_reasons: List[str] = Field(default_factory=list)
    evidence_freshness_status: Literal["FRESH", "AGING", "STALE", "UNKNOWN"] = "UNKNOWN"
    stale_artifact_count: int = Field(default=0, ge=0)
    freshness_summary_line: str = ""
    artifact_freshness: List[OracleArtifactFreshnessItem] = Field(default_factory=list)
    artifact_lineage_summary_line: str = ""
    artifact_lineage: List[OracleArtifactLineageItem] = Field(default_factory=list)
    evidence_integrity_status: OracleArtifactIntegrityStatus = "UNKNOWN"
    unverified_artifact_count: int = Field(default=0, ge=0)
    integrity_summary_line: str = ""
    evidence_coverage_status: OracleArtifactCoverageStatus = "UNKNOWN"
    missing_expected_artifact_count: int = Field(default=0, ge=0)
    evidence_coverage_summary_line: str = ""
    missing_expected_artifact_labels: List[str] = Field(default_factory=list)
    support_verification_status: OracleSupportVerificationStatus = "ABSENT"
    support_verification_summary_line: str = ""
    support_verification_paths: List[str] = Field(default_factory=list)
    support_chain_trust_status: OracleConstitutionalTrustStatus = "TRUST_RESTRICTED"
    support_chain_trust_summary_line: str = ""
    support_chain_trust_reasons: List[str] = Field(default_factory=list)
    support_chain_remediation_status: OracleSupportChainRemediationStatus = "REMEDIATION_RECOMMENDED"
    support_chain_remediation_summary_line: str = ""
    support_chain_remediation_actions: List[str] = Field(default_factory=list)
    trust_plane_summary_line: str = ""
    operator_reliance_posture: OracleReliancePosture = "CAUTIOUS_ADVISORY_ONLY"
    operator_reliance_summary_line: str = ""
    operator_reliance_reasons: List[str] = Field(default_factory=list)
    operator_escalation_lane: OracleEscalationLane = "HEIGHTENED_OPERATOR_ESCALATION"
    operator_escalation_summary_line: str = ""
    operator_escalation_reasons: List[str] = Field(default_factory=list)
    propagation_posture: OraclePropagationPosture = "REVIEW_ONLY_PROPAGATION"
    propagation_summary_line: str = ""
    propagation_reasons: List[str] = Field(default_factory=list)
    automation_posture: OracleAutomationPosture = "AUTOMATION_REVIEW_REQUIRED"
    automation_summary_line: str = ""
    automation_reasons: List[str] = Field(default_factory=list)
    control_plane_summary_line: str = ""
    governance_plane_status: OracleGovernancePlaneStatus = "GOVERNANCE_RESTRICTED"
    governance_plane_summary_line: str = ""
    governance_plane_reasons: List[str] = Field(default_factory=list)
    governance_plane_codes: List[OracleGovernanceCode] = Field(default_factory=list)
    governance_plane_blocking_dimensions: List[OracleGovernanceDimension] = Field(default_factory=list)
    governance_plane_restricted_dimensions: List[OracleGovernanceDimension] = Field(default_factory=list)
    governance_plane_actions: List[str] = Field(default_factory=list)
    governance_plane_action_items: List[OracleGovernanceActionItem] = Field(default_factory=list)
    governance_plane_primary_dimension: OracleGovernanceDimension | None = None
    governance_plane_primary_severity: OracleGovernancePrimarySeverity = "READY"
    governance_plane_primary_action_text: str = ""
    governance_plane_priority_band: OracleGovernancePriorityBand = "ROUTINE_PRIORITY"
    governance_plane_priority_score: int = Field(default=0, ge=0, le=100)
    governance_plane_priority_summary_line: str = ""
    governance_plane_review_target: OracleGovernanceReviewTarget = "ROUTINE_REVIEW_QUEUE"
    governance_plane_review_sla_hours: int = Field(default=72, ge=1, le=168)
    governance_plane_review_summary_line: str = ""
    governance_plane_review_due_by_utc: datetime | None = None
    governance_plane_review_sort_key: str = ""
    governance_plane_review_envelope_vector: str = ""
    governance_plane_review_envelope_sha256: str = ""
    governance_plane_routing_summary_line: str = ""
    governance_plane_routing_vector: str = ""
    governance_plane_routing_sha256: str = ""
    governance_plane_dispatch_summary_line: str = ""
    governance_plane_dispatch_vector: str = ""
    governance_plane_dispatch_sha256: str = ""
    governance_plane_dispatch_claim_key: str = ""
    governance_plane_dispatch_posture: OracleGovernanceDispatchPosture = "DISPATCH_REVIEW_ONLY"
    governance_plane_dispatch_permitted: bool = False
    governance_plane_dispatch_reasons: List[str] = Field(default_factory=list)
    governance_plane_dispatch_timeliness: OracleGovernanceDispatchTimeliness = "DISPATCH_ACTIVE"
    governance_plane_dispatch_claim_permitted_now: bool = False
    governance_plane_dispatch_timeliness_summary_line: str = ""
    governance_plane_dispatch_claim_urgency: OracleGovernanceDispatchClaimUrgency = "DO_NOT_CLAIM"
    governance_plane_dispatch_claim_score: int = Field(default=0, ge=0, le=100)
    governance_plane_dispatch_claim_summary_line: str = ""
    governance_plane_claim_summary_line: str = ""
    governance_plane_claim_queue_key: OracleGovernanceQueueKey = ""
    governance_plane_claim_review_target: OracleGovernanceReviewTarget = "ROUTINE_REVIEW_QUEUE"
    governance_plane_claim_priority_band: OracleGovernancePriorityBand = "ROUTINE_PRIORITY"
    governance_plane_claim_review_due_by_utc: datetime | None = None
    governance_plane_claim_review_sort_key: str = ""
    governance_plane_claim_route_sha256: str = ""
    governance_plane_claim_review_envelope_sha256: str = ""
    governance_plane_claim_routing_envelope_sha256: str = ""
    governance_plane_claim_dispatch_claim_key: str = ""
    governance_plane_claim_dispatch_sha256: str = ""
    governance_plane_claim_codes: List[OracleGovernanceClaimCode] = Field(default_factory=list)
    governance_plane_claim_primary_code: OracleGovernanceClaimCode | None = None
    governance_plane_claim_action_items: List[OracleGovernanceClaimActionItem] = Field(default_factory=list)
    governance_plane_claim_primary_action_text: str = ""
    governance_plane_claim_worker_lane: OracleGovernanceClaimWorkerLane = "ROUTINE_CLAIM_WORKER"
    governance_plane_claim_worker_summary_line: str = ""
    governance_plane_claim_worker_sort_key: str = ""
    governance_plane_claim_lease_key: str = ""
    governance_plane_claim_lease_mode: OracleGovernanceClaimLeaseMode = "STANDARD_LEASE"
    governance_plane_claim_lease_ttl_seconds: int = 0
    governance_plane_claim_lease_expires_at_utc: Optional[datetime] = None
    governance_plane_claim_lease_active_now: bool = False
    governance_plane_claim_lease_summary_line: str = ""
    governance_plane_claim_lease_coverage: OracleGovernanceClaimLeaseCoverage = "NO_LEASE_COVERAGE"
    governance_plane_claim_lease_coverage_summary_line: str = ""
    governance_plane_claim_lease_health: OracleGovernanceClaimLeaseHealth = "LEASE_BLOCKED"
    governance_plane_claim_lease_health_summary_line: str = ""
    governance_plane_claim_lease_renewal_posture: OracleGovernanceClaimLeaseRenewalPosture = "NO_RENEWAL"
    governance_plane_claim_lease_renewal_permitted_now: bool = False
    governance_plane_claim_lease_renewal_summary_line: str = ""
    governance_plane_claim_lease_action: OracleGovernanceClaimLeaseAction = "NO_LEASE_ACTION"
    governance_plane_claim_lease_action_summary_line: str = ""
    governance_plane_claim_disposition: OracleGovernanceClaimDisposition = "CLAIM_QUEUE_ROUTINE"
    governance_plane_claim_disposition_summary_line: str = ""
    governance_plane_claim_process_posture: OracleGovernanceClaimProcessPosture = "PROCESS_QUEUE_ONLY"
    governance_plane_claim_process_permitted_now: bool = False
    governance_plane_claim_process_summary_line: str = ""
    governance_plane_claim_operability: OracleGovernanceClaimOperability = "CLAIM_INOPERABLE"
    governance_plane_claim_operability_summary_line: str = ""
    governance_plane_claim_vector: str = ""
    governance_plane_claim_sha256: str = ""
    governance_plane_queue_key: OracleGovernanceQueueKey = ""
    governance_plane_route_vector: str = ""
    governance_plane_route_sha256: str = ""
    governance_plane_vector: str = ""
    governance_plane_sha256: str = ""
    trust_status: OracleConstitutionalTrustStatus
    preferred_strategic_backing_source: str | None = None
    exact_feedback_confirmation_count: int = Field(default=0, ge=0)
    exact_feedback_relief_count: int = Field(default=0, ge=0)
    exact_cadence_signal_classification: Literal["EXACT_CONFIRMED_PRESSURE", "EXACT_RELIEF_PRESSURE", "AMBIENT_DRIFT"] = "AMBIENT_DRIFT"
    preferred_strategic_backing_classification: Literal["SEALED_STRATEGIC_STACK_BACKED", "DOCTRINE_ONLY_LADDER_BACKED", "NO_STRATEGIC_STACK_HISTORY"] | None = None
    summary_line: str
    status_pack_digest_sha256: str
    incident_pack_digest_sha256: str | None = None
    sections: List[OracleBriefingSection] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    provenance_digest_sha256: str = ""

    model_config = {"extra": "forbid"}


class OracleCompactedStateInspectionReport(BaseModel):
    schema_version: Literal["oracle_compacted_state_inspection_report/v1"] = "oracle_compacted_state_inspection_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    view_label: str
    source_event_log_path: str
    replay_status: Literal["CURRENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"]
    current_file_size_bytes: int = Field(ge=0)
    metadata_file_size_bytes: int = Field(ge=0)
    metadata_file_offset_bytes: int = Field(ge=0)
    last_event_log_sequence_number: int | None = None
    last_event_log_entry_hash: str | None = None
    cached_window_entry_count: int = Field(ge=0)
    cached_window_entry_ids: List[str] = Field(default_factory=list)
    query_spec: OracleEventLogQuerySpec = Field(default_factory=OracleEventLogQuerySpec)
    compacted_window_digest_sha256: str = ""
    summary_line: str
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleReplayAuditSource(BaseModel):
    source_id: Literal["canonical_event_log", "checkpoint_metadata", "checkpoint_manifest", "checkpoint_verification", "rebuilt_checkpoint_metadata", "derived_view_report"]
    status: Literal["CONSISTENT", "STALE", "DRIFTED", "CORRUPTED", "SKIPPED"]
    summary_line: str
    details: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}


class OracleReplayAuditReport(BaseModel):
    schema_version: Literal["oracle_replay_audit_report/v1"] = "oracle_replay_audit_report/v1"
    generated_at_utc: datetime
    lane_path: str
    checkpoint_metadata_path: str
    report_path: str | None = None
    checkpoint_manifest_path: str | None = None
    checkpoint_verification_path: str | None = None
    replay_status: Literal["CONSISTENT", "STALE", "DRIFTED", "CORRUPTED", "SOURCE_MISSING"]
    canonical_window_digest_sha256: str = ""
    compacted_window_digest_sha256: str = ""
    rebuilt_window_digest_sha256: str = ""
    compared_entry_ids: List[str] = Field(default_factory=list)
    findings: List[str] = Field(default_factory=list)
    operator_actions: List[str] = Field(default_factory=list)
    sources: List[OracleReplayAuditSource] = Field(default_factory=list)
    summary_line: str

    model_config = {"extra": "forbid"}

