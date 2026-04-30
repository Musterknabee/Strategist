from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import (
    _proposal_digest_for_semantic_gate,
    _semantic_evidence_checksums,
    _sha256_payload,
)
from strategy_validator.application.research_integrity_preflight import build_semantic_research_adjudication_gate_summary
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationReadinessIssue,
    SemanticAdjudicationReadinessReport,
    SemanticResearchGateArtifact,
    SemanticResearchGateArtifactIssue,
    SemanticResearchGateArtifactVerificationReport,
)


def _gate_artifact_checksum_payload(artifact: SemanticResearchGateArtifact) -> dict[str, Any]:
    payload = artifact.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_research_gate_artifact(
    proposal: ExperimentManifest,
    *,
    require_semantic_evidence: bool | None = None,
    require_data_spine_seal: bool | None = None,
) -> SemanticResearchGateArtifact:
    """Build a deterministic machine-readable artifact for the semantic adjudication gate."""
    summary = build_semantic_research_adjudication_gate_summary(
        proposal,
        require_semantic_evidence=require_semantic_evidence,
        require_data_spine_seal=require_data_spine_seal,
    )
    proposal_digest = _proposal_digest_for_semantic_gate(proposal)
    seal = proposal.evidence_bundle.data_spine_seal
    base = SemanticResearchGateArtifact(
        artifact_id="pending",
        experiment_id=proposal.experiment_id,
        proposal_digest=proposal_digest,
        summary=summary,
        semantic_evidence_checksums=_semantic_evidence_checksums(proposal),
        data_spine_fingerprint=None if seal is None else seal.fingerprint,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_gate_artifact_checksum_payload(base))
    artifact_id = f"semantic-gate-{proposal.experiment_id}-{checksum[:16]}"
    final = base.model_copy(update={"artifact_id": artifact_id, "payload_checksum": checksum})
    # The artifact id is part of the payload, so recompute once with the stable id.
    final_checksum = _sha256_payload(_gate_artifact_checksum_payload(final))
    return final.model_copy(update={"payload_checksum": final_checksum})


def verify_semantic_research_gate_artifact(
    artifact: SemanticResearchGateArtifact,
    *,
    proposal: ExperimentManifest | None = None,
) -> SemanticResearchGateArtifactVerificationReport:
    """Verify a semantic adjudication-gate artifact against itself and optionally its source proposal."""
    issues: list[SemanticResearchGateArtifactIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticResearchGateArtifactIssue(code=code, message=message, severity=severity))

    observed_checksum = artifact.payload_checksum
    expected_checksum = _sha256_payload(_gate_artifact_checksum_payload(artifact))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_GATE_ARTIFACT_CHECKSUM_MISMATCH", "artifact payload checksum does not match canonical payload")

    if artifact.schema_version != "semantic_research_gate_artifact/v1":
        issue("SEMANTIC_GATE_ARTIFACT_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic gate artifact schema version")

    if artifact.experiment_id != artifact.summary.experiment_id:
        issue("SEMANTIC_GATE_ARTIFACT_EXPERIMENT_MISMATCH", "artifact experiment_id differs from summary experiment_id")

    if proposal is not None:
        expected_digest = _proposal_digest_for_semantic_gate(proposal)
        if artifact.experiment_id != proposal.experiment_id:
            issue("SEMANTIC_GATE_ARTIFACT_PROPOSAL_EXPERIMENT_MISMATCH", "artifact experiment_id differs from proposal experiment_id")
        if artifact.proposal_digest != expected_digest:
            issue("SEMANTIC_GATE_ARTIFACT_PROPOSAL_DIGEST_MISMATCH", "artifact proposal digest differs from current proposal semantic gate inputs")
        expected_artifact = build_semantic_research_gate_artifact(proposal)
        if artifact.summary != expected_artifact.summary:
            issue("SEMANTIC_GATE_ARTIFACT_SUMMARY_DRIFT", "artifact summary differs from recomputed semantic adjudication gate summary")
        if artifact.semantic_evidence_checksums != expected_artifact.semantic_evidence_checksums:
            issue("SEMANTIC_GATE_ARTIFACT_EVIDENCE_CHECKSUM_DRIFT", "artifact evidence checksum list differs from proposal")
        if artifact.data_spine_fingerprint != expected_artifact.data_spine_fingerprint:
            issue("SEMANTIC_GATE_ARTIFACT_DATA_SPINE_DRIFT", "artifact Data Spine fingerprint differs from proposal")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticResearchGateArtifactVerificationReport(
        artifact_id=artifact.artifact_id,
        experiment_id=artifact.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_GATE_ARTIFACT" if verified else "REBUILD_SEMANTIC_GATE_ARTIFACT",
    )


def build_semantic_adjudication_readiness_report(
    proposal: ExperimentManifest,
    *,
    gate_artifact: SemanticResearchGateArtifact | None = None,
    require_gate_artifact: bool = False,
    require_semantic_evidence: bool | None = None,
    require_data_spine_seal: bool | None = None,
) -> SemanticAdjudicationReadinessReport:
    """Build the final semantic-lane handoff report before adjudication.

    This does not mutate the proposal and does not call the orchestrator. It
    combines the canonical semantic integrity gate with optional verification of
    the sealed gate artifact that operators can archive with an adjudication
    handoff bundle.
    """
    summary = build_semantic_research_adjudication_gate_summary(
        proposal,
        require_semantic_evidence=require_semantic_evidence,
        require_data_spine_seal=require_data_spine_seal,
    )
    issues: list[SemanticAdjudicationReadinessIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationReadinessIssue(code=code, message=message, severity=severity))

    for code in summary.blocker_codes:
        issue(code, "semantic adjudication gate reported a blocker")
    for code in summary.warning_codes:
        issue(code, "semantic adjudication gate reported a warning", severity="WARNING")

    gate_artifact_verified: bool | None = None
    gate_artifact_id: str | None = None
    gate_artifact_checksum: str | None = None
    if gate_artifact is None:
        if require_gate_artifact and summary.semantic_lane_present:
            issue(
                "SEMANTIC_GATE_ARTIFACT_REQUIRED",
                "semantic lane is present but no sealed semantic gate artifact was provided",
            )
    else:
        gate_artifact_id = gate_artifact.artifact_id
        gate_artifact_checksum = gate_artifact.payload_checksum
        artifact_report = verify_semantic_research_gate_artifact(gate_artifact, proposal=proposal)
        gate_artifact_verified = artifact_report.verified
        for artifact_issue in artifact_report.issues:
            issue(artifact_issue.code, artifact_issue.message, severity=artifact_issue.severity)

    blocker_codes = [item.code for item in issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in issues if item.severity != "BLOCKER"]
    ready = summary.gate_passed and not blocker_codes
    return SemanticAdjudicationReadinessReport(
        experiment_id=proposal.experiment_id,
        ready_for_adjudication=ready,
        semantic_lane_present=summary.semantic_lane_present,
        gate_passed=summary.gate_passed,
        gate_artifact_required=require_gate_artifact,
        gate_artifact_present=gate_artifact is not None,
        gate_artifact_verified=gate_artifact_verified,
        gate_artifact_id=gate_artifact_id,
        gate_artifact_checksum=gate_artifact_checksum,
        semantic_summary=summary,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_count=len(issues),
        issues=issues,
        recommended_action="HAND_TO_ADJUDICATOR" if ready else "BLOCK_ADJUDICATION_HANDOFF",
    )


__all__ = [
    "build_semantic_research_gate_artifact",
    "verify_semantic_research_gate_artifact",
    "build_semantic_adjudication_readiness_report",
]
