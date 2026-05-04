from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_gate_artifact import (
    SemanticAdjudicationReadinessReport,
    SemanticResearchGateArtifact,
)

class SemanticAdjudicationHandoffArtifact(SemanticBaseModel):
    """Sealed operator handoff artifact for semantic research adjudication readiness."""

    schema_version: NonEmptyString = "semantic_adjudication_handoff_artifact/v1"
    artifact_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    readiness_report: SemanticAdjudicationReadinessReport
    gate_artifact: SemanticResearchGateArtifact | None = None
    payload_checksum: NonEmptyString

class SemanticAdjudicationHandoffArtifactIssue(SemanticBaseModel):
    """Verification issue for a semantic adjudication handoff artifact."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticAdjudicationHandoffArtifactVerificationReport(SemanticBaseModel):
    """Verification report for the final semantic adjudication handoff artifact."""

    schema_version: NonEmptyString = "semantic_adjudication_handoff_artifact_verification/v1"
    artifact_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationHandoffArtifactIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticAdjudicationBundle(SemanticBaseModel):
    """Replayable operator bundle for final semantic adjudication handoff.

    The bundle keeps the proposal-side semantic input digest together with the
    sealed gate and handoff artifacts. It is intentionally compact and does not
    embed the full proposal, so operators can archive/transport the handoff
    proof without copying potentially large proposal payloads.
    """

    schema_version: NonEmptyString = "semantic_adjudication_bundle/v1"
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    gate_artifact: SemanticResearchGateArtifact | None = None
    handoff_artifact: SemanticAdjudicationHandoffArtifact
    semantic_evidence_checksums: list[str] = Field(default_factory=list)
    data_spine_fingerprint: str | None = None
    payload_checksum: NonEmptyString

class SemanticAdjudicationBundleIssue(SemanticBaseModel):
    """Verification issue for a semantic adjudication handoff bundle."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticAdjudicationBundleVerificationReport(SemanticBaseModel):
    """Verification report for the final semantic adjudication bundle."""

    schema_version: NonEmptyString = "semantic_adjudication_bundle_verification/v1"
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationBundleIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticAdjudicationBundleSummary(SemanticBaseModel):
    """Compact operator/CI summary for semantic adjudication bundle readiness."""

    schema_version: NonEmptyString = "semantic_adjudication_bundle_summary/v1"
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    ready_for_adjudication: bool
    recommended_action: NonEmptyString
    gate_passed: bool
    gate_artifact_present: bool
    handoff_artifact_present: bool
    semantic_evidence_count: int = Field(ge=0)
    data_spine_fingerprint_present: bool
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

