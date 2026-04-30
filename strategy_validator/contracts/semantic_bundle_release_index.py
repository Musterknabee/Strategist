from __future__ import annotations

from pydantic import Field

from strategy_validator.contracts.semantic_core import NonEmptyString, SemanticBaseModel
from strategy_validator.contracts.semantic_adjudication_bundle import SemanticAdjudicationBundleSummary

class SemanticAdjudicationBundleManifest(SemanticBaseModel):
    """Portable manifest for archiving or releasing a semantic adjudication bundle."""

    schema_version: NonEmptyString = "semantic_adjudication_bundle_manifest/v1"
    manifest_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    bundle_payload_checksum: NonEmptyString
    gate_artifact_id: str | None = None
    gate_artifact_checksum: str | None = None
    handoff_artifact_id: NonEmptyString
    handoff_artifact_checksum: NonEmptyString
    semantic_evidence_checksums: list[str] = Field(default_factory=list)
    data_spine_fingerprint: str | None = None
    summary: SemanticAdjudicationBundleSummary
    payload_checksum: NonEmptyString

class SemanticAdjudicationBundleManifestIssue(SemanticBaseModel):
    """Verification issue for a semantic adjudication bundle manifest."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticAdjudicationBundleManifestVerificationReport(SemanticBaseModel):
    """Verification report for a semantic adjudication bundle manifest."""

    schema_version: NonEmptyString = "semantic_adjudication_bundle_manifest_verification/v1"
    manifest_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationBundleManifestIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

class SemanticAdjudicationBundleReleasePreflightReport(SemanticBaseModel):
    """Operator/CI preflight report for a sealed semantic adjudication bundle release.

    This is the compact handoff object intended for release checks: it verifies
    the bundle, verifies the portable manifest when supplied/required, and
    repeats the final adjudication readiness recommendation without embedding
    the full proposal.
    """

    schema_version: NonEmptyString = "semantic_adjudication_bundle_release_preflight/v1"
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    manifest_id: str | None = None
    bundle_verified: bool
    manifest_required: bool
    manifest_verified: bool
    ready_for_adjudication: bool
    recommended_action: NonEmptyString
    bundle_payload_checksum: NonEmptyString
    manifest_payload_checksum: str | None = None
    semantic_evidence_count: int = Field(ge=0)
    data_spine_fingerprint_present: bool
    gate_artifact_present: bool
    handoff_artifact_present: bool
    blocker_codes: list[str] = Field(default_factory=list)
    warning_codes: list[str] = Field(default_factory=list)
    bundle_issue_codes: list[str] = Field(default_factory=list)
    manifest_issue_codes: list[str] = Field(default_factory=list)
    issue_count: int = Field(ge=0)

class SemanticAdjudicationBundleReleaseIndex(SemanticBaseModel):
    """Portable index for the final semantic adjudication release handoff.

    The index is intentionally small enough to use as a CI artifact or release
    manifest pointer. It binds the bundle, manifest, gate artifact, handoff
    artifact, semantic evidence checksums, and the final release preflight
    recommendation into one checksummed object.
    """

    schema_version: NonEmptyString = "semantic_adjudication_bundle_release_index/v1"
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    proposal_digest: NonEmptyString
    bundle_payload_checksum: NonEmptyString
    manifest_id: str | None = None
    manifest_payload_checksum: str | None = None
    gate_artifact_id: str | None = None
    gate_artifact_checksum: str | None = None
    handoff_artifact_id: NonEmptyString
    handoff_artifact_checksum: NonEmptyString
    semantic_evidence_checksums: list[str] = Field(default_factory=list)
    data_spine_fingerprint: str | None = None
    release_preflight: SemanticAdjudicationBundleReleasePreflightReport
    payload_checksum: NonEmptyString

class SemanticAdjudicationBundleReleaseIndexIssue(SemanticBaseModel):
    """Verification issue for a semantic adjudication bundle release index."""

    code: NonEmptyString
    message: NonEmptyString
    severity: NonEmptyString = "BLOCKER"

class SemanticAdjudicationBundleReleaseIndexVerificationReport(SemanticBaseModel):
    """Verification report for a semantic adjudication release index."""

    schema_version: NonEmptyString = "semantic_adjudication_bundle_release_index_verification/v1"
    index_id: NonEmptyString
    bundle_id: NonEmptyString
    experiment_id: NonEmptyString
    verified: bool
    expected_payload_checksum: NonEmptyString
    observed_payload_checksum: NonEmptyString
    issue_count: int = Field(ge=0)
    issue_codes: list[str] = Field(default_factory=list)
    issues: list[SemanticAdjudicationBundleReleaseIndexIssue] = Field(default_factory=list)
    recommended_action: NonEmptyString

