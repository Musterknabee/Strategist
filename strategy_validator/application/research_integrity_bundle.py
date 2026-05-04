from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import (
    _proposal_digest_for_semantic_gate,
    _semantic_evidence_checksums,
    _sha256_payload,
)
from strategy_validator.application.research_integrity_gate_artifact import (
    build_semantic_adjudication_readiness_report,
    build_semantic_research_gate_artifact,
    verify_semantic_research_gate_artifact,
)
from strategy_validator.application.research_integrity_preflight import _semantic_lane_present
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleIssue,
    SemanticAdjudicationBundleSummary,
    SemanticAdjudicationBundleVerificationReport,
    SemanticAdjudicationHandoffArtifact,
    SemanticAdjudicationHandoffArtifactIssue,
    SemanticAdjudicationHandoffArtifactVerificationReport,
    SemanticResearchGateArtifact,
)


def _handoff_artifact_payload(artifact: SemanticAdjudicationHandoffArtifact) -> dict[str, Any]:
    payload = artifact.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def _handoff_payload_checksum(artifact: SemanticAdjudicationHandoffArtifact) -> str:
    return _sha256_payload(_handoff_artifact_payload(artifact))


def build_semantic_adjudication_handoff_artifact(
    proposal: ExperimentManifest,
    *,
    gate_artifact: SemanticResearchGateArtifact | None = None,
    require_gate_artifact: bool = False,
    require_semantic_evidence: bool | None = None,
    require_data_spine_seal: bool | None = None,
) -> SemanticAdjudicationHandoffArtifact:
    """Build a sealed operator handoff artifact for semantic adjudication readiness.

    This artifact is intentionally read-only: it packages the final readiness
    report, optional sealed semantic gate artifact, and a digest of the proposal
    semantic inputs that the adjudication gate depends on. Operators can archive
    it with a handoff bundle and later verify that the proposal inputs have not
    drifted.
    """
    readiness = build_semantic_adjudication_readiness_report(
        proposal,
        gate_artifact=gate_artifact,
        require_gate_artifact=require_gate_artifact,
        require_semantic_evidence=require_semantic_evidence,
        require_data_spine_seal=require_data_spine_seal,
    )
    proposal_digest = _proposal_digest_for_semantic_gate(proposal)
    seed_payload = {
        "schema_version": "semantic_adjudication_handoff_artifact/v1",
        "experiment_id": proposal.experiment_id,
        "proposal_digest": proposal_digest,
        "readiness_report": readiness.model_dump(mode="json"),
        "gate_artifact": None if gate_artifact is None else gate_artifact.model_dump(mode="json"),
    }
    artifact_id = f"semantic-handoff-{proposal.experiment_id}-{_sha256_payload(seed_payload)[:16]}"
    artifact = SemanticAdjudicationHandoffArtifact(
        artifact_id=artifact_id,
        experiment_id=proposal.experiment_id,
        proposal_digest=proposal_digest,
        readiness_report=readiness,
        gate_artifact=gate_artifact,
        payload_checksum="pending",
    )
    return artifact.model_copy(update={"payload_checksum": _handoff_payload_checksum(artifact)})


def verify_semantic_adjudication_handoff_artifact(
    artifact: SemanticAdjudicationHandoffArtifact,
    *,
    proposal: ExperimentManifest | None = None,
) -> SemanticAdjudicationHandoffArtifactVerificationReport:
    """Verify a semantic adjudication handoff artifact against itself and a proposal.

    With a proposal supplied, this recomputes the readiness report using the
    artifact's own gate-artifact requirement and optional embedded gate artifact.
    """
    issues: list[SemanticAdjudicationHandoffArtifactIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationHandoffArtifactIssue(code=code, message=message, severity=severity))

    observed_checksum = artifact.payload_checksum
    expected_checksum = _handoff_payload_checksum(artifact)
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_HANDOFF_ARTIFACT_CHECKSUM_MISMATCH", "handoff artifact payload checksum does not match canonical payload")

    if artifact.schema_version != "semantic_adjudication_handoff_artifact/v1":
        issue("SEMANTIC_HANDOFF_ARTIFACT_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic handoff artifact schema version")

    if artifact.experiment_id != artifact.readiness_report.experiment_id:
        issue("SEMANTIC_HANDOFF_ARTIFACT_EXPERIMENT_MISMATCH", "handoff artifact experiment_id differs from readiness report")

    if artifact.gate_artifact is not None:
        gate_report = verify_semantic_research_gate_artifact(artifact.gate_artifact, proposal=proposal)
        for gate_issue in gate_report.issues:
            issue(gate_issue.code, gate_issue.message, severity=gate_issue.severity)
        if artifact.readiness_report.gate_artifact_id != artifact.gate_artifact.artifact_id:
            issue("SEMANTIC_HANDOFF_GATE_ARTIFACT_ID_MISMATCH", "embedded gate artifact id differs from readiness report")
        if artifact.readiness_report.gate_artifact_checksum != artifact.gate_artifact.payload_checksum:
            issue("SEMANTIC_HANDOFF_GATE_ARTIFACT_CHECKSUM_MISMATCH", "embedded gate artifact checksum differs from readiness report")

    if proposal is not None:
        if artifact.experiment_id != proposal.experiment_id:
            issue("SEMANTIC_HANDOFF_PROPOSAL_EXPERIMENT_MISMATCH", "handoff artifact experiment_id differs from proposal experiment_id")
        expected_digest = _proposal_digest_for_semantic_gate(proposal)
        if artifact.proposal_digest != expected_digest:
            issue("SEMANTIC_HANDOFF_PROPOSAL_DIGEST_MISMATCH", "handoff artifact proposal digest differs from current proposal semantic gate inputs")
        expected_readiness = build_semantic_adjudication_readiness_report(
            proposal,
            gate_artifact=artifact.gate_artifact,
            require_gate_artifact=artifact.readiness_report.gate_artifact_required,
        )
        if artifact.readiness_report != expected_readiness:
            issue("SEMANTIC_HANDOFF_READINESS_DRIFT", "handoff readiness report differs from recomputed readiness report")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationHandoffArtifactVerificationReport(
        artifact_id=artifact.artifact_id,
        experiment_id=artifact.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_ADJUDICATION_HANDOFF" if verified else "REBUILD_SEMANTIC_ADJUDICATION_HANDOFF",
    )

def _bundle_artifact_payload(bundle: SemanticAdjudicationBundle) -> dict[str, Any]:
    payload = bundle.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def _bundle_payload_checksum(bundle: SemanticAdjudicationBundle) -> str:
    return _sha256_payload(_bundle_artifact_payload(bundle))


def build_semantic_adjudication_bundle(
    proposal: ExperimentManifest,
    *,
    gate_artifact: SemanticResearchGateArtifact | None = None,
    handoff_artifact: SemanticAdjudicationHandoffArtifact | None = None,
    require_gate_artifact: bool = True,
    require_semantic_evidence: bool | None = None,
    require_data_spine_seal: bool | None = None,
) -> SemanticAdjudicationBundle:
    """Build the compact operator bundle for final semantic adjudication handoff.

    The bundle is the highest-level semantic handoff artifact: it binds the
    sealed gate artifact, final readiness/handoff artifact, proposal semantic
    input digest, semantic evidence checksums, and Data Spine fingerprint.
    """
    if gate_artifact is None and require_gate_artifact and _semantic_lane_present(proposal):
        gate_artifact = build_semantic_research_gate_artifact(
            proposal,
            require_semantic_evidence=require_semantic_evidence,
            require_data_spine_seal=require_data_spine_seal,
        )
    if handoff_artifact is None:
        handoff_artifact = build_semantic_adjudication_handoff_artifact(
            proposal,
            gate_artifact=gate_artifact,
            require_gate_artifact=require_gate_artifact,
            require_semantic_evidence=require_semantic_evidence,
            require_data_spine_seal=require_data_spine_seal,
        )
    proposal_digest = _proposal_digest_for_semantic_gate(proposal)
    seal = proposal.evidence_bundle.data_spine_seal
    seed_payload = {
        "schema_version": "semantic_adjudication_bundle/v1",
        "experiment_id": proposal.experiment_id,
        "proposal_digest": proposal_digest,
        "gate_artifact_id": None if gate_artifact is None else gate_artifact.artifact_id,
        "handoff_artifact_id": handoff_artifact.artifact_id,
    }
    bundle = SemanticAdjudicationBundle(
        bundle_id=f"semantic-bundle-{proposal.experiment_id}-{_sha256_payload(seed_payload)[:16]}",
        experiment_id=proposal.experiment_id,
        proposal_digest=proposal_digest,
        gate_artifact=gate_artifact,
        handoff_artifact=handoff_artifact,
        semantic_evidence_checksums=_semantic_evidence_checksums(proposal),
        data_spine_fingerprint=None if seal is None else seal.fingerprint,
        payload_checksum="pending",
    )
    return bundle.model_copy(update={"payload_checksum": _bundle_payload_checksum(bundle)})


def verify_semantic_adjudication_bundle(
    bundle: SemanticAdjudicationBundle,
    *,
    proposal: ExperimentManifest | None = None,
) -> SemanticAdjudicationBundleVerificationReport:
    """Verify a semantic adjudication bundle against itself and optionally a proposal."""
    issues: list[SemanticAdjudicationBundleIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticAdjudicationBundleIssue(code=code, message=message, severity=severity))

    observed_checksum = bundle.payload_checksum
    expected_checksum = _bundle_payload_checksum(bundle)
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_BUNDLE_CHECKSUM_MISMATCH", "bundle payload checksum does not match canonical payload")

    if bundle.schema_version != "semantic_adjudication_bundle/v1":
        issue("SEMANTIC_BUNDLE_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic adjudication bundle schema version")

    if bundle.experiment_id != bundle.handoff_artifact.experiment_id:
        issue("SEMANTIC_BUNDLE_HANDOFF_EXPERIMENT_MISMATCH", "bundle experiment_id differs from handoff artifact")
    if bundle.proposal_digest != bundle.handoff_artifact.proposal_digest:
        issue("SEMANTIC_BUNDLE_HANDOFF_PROPOSAL_DIGEST_MISMATCH", "bundle proposal digest differs from handoff artifact proposal digest")

    if bundle.gate_artifact is not None:
        if bundle.gate_artifact.experiment_id != bundle.experiment_id:
            issue("SEMANTIC_BUNDLE_GATE_EXPERIMENT_MISMATCH", "gate artifact experiment_id differs from bundle")
        if bundle.handoff_artifact.gate_artifact is None:
            issue("SEMANTIC_BUNDLE_GATE_NOT_EMBEDDED_IN_HANDOFF", "bundle has a gate artifact but handoff artifact does not embed one")
        elif bundle.handoff_artifact.gate_artifact.artifact_id != bundle.gate_artifact.artifact_id:
            issue("SEMANTIC_BUNDLE_GATE_ID_MISMATCH", "bundle gate artifact differs from handoff embedded gate artifact")
        gate_report = verify_semantic_research_gate_artifact(bundle.gate_artifact, proposal=proposal)
        for gate_issue in gate_report.issues:
            issue(gate_issue.code, gate_issue.message, severity=gate_issue.severity)

    handoff_report = verify_semantic_adjudication_handoff_artifact(bundle.handoff_artifact, proposal=proposal)
    for handoff_issue in handoff_report.issues:
        issue(handoff_issue.code, handoff_issue.message, severity=handoff_issue.severity)

    if proposal is not None:
        expected_digest = _proposal_digest_for_semantic_gate(proposal)
        expected_checksums = _semantic_evidence_checksums(proposal)
        expected_fingerprint = None if proposal.evidence_bundle.data_spine_seal is None else proposal.evidence_bundle.data_spine_seal.fingerprint
        if bundle.experiment_id != proposal.experiment_id:
            issue("SEMANTIC_BUNDLE_PROPOSAL_EXPERIMENT_MISMATCH", "bundle experiment_id differs from proposal experiment_id")
        if bundle.proposal_digest != expected_digest:
            issue("SEMANTIC_BUNDLE_PROPOSAL_DIGEST_MISMATCH", "bundle proposal digest differs from current proposal semantic gate inputs")
        if bundle.semantic_evidence_checksums != expected_checksums:
            issue("SEMANTIC_BUNDLE_EVIDENCE_CHECKSUM_DRIFT", "bundle semantic evidence checksums differ from proposal")
        if bundle.data_spine_fingerprint != expected_fingerprint:
            issue("SEMANTIC_BUNDLE_DATA_SPINE_DRIFT", "bundle Data Spine fingerprint differs from proposal")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationBundleVerificationReport(
        bundle_id=bundle.bundle_id,
        experiment_id=bundle.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_ADJUDICATION_BUNDLE" if verified else "REBUILD_SEMANTIC_ADJUDICATION_BUNDLE",
    )



def summarize_semantic_adjudication_bundle(
    bundle: SemanticAdjudicationBundle,
    *,
    proposal: ExperimentManifest | None = None,
) -> SemanticAdjudicationBundleSummary:
    """Build a compact operator/CI summary for a semantic adjudication bundle."""
    verification = verify_semantic_adjudication_bundle(bundle, proposal=proposal)
    readiness = bundle.handoff_artifact.readiness_report
    blocker_codes = [item.code for item in verification.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in verification.issues if item.severity != "BLOCKER"]
    for code in readiness.blocker_codes:
        if code not in blocker_codes:
            blocker_codes.append(code)
    for code in readiness.warning_codes:
        if code not in warning_codes and code not in blocker_codes:
            warning_codes.append(code)
    ready = verification.verified and readiness.ready_for_adjudication
    return SemanticAdjudicationBundleSummary(
        bundle_id=bundle.bundle_id,
        experiment_id=bundle.experiment_id,
        verified=verification.verified,
        ready_for_adjudication=ready,
        recommended_action="HAND_TO_ADJUDICATOR" if ready else "BLOCK_SEMANTIC_ADJUDICATION_BUNDLE",
        gate_passed=readiness.gate_passed,
        gate_artifact_present=bundle.gate_artifact is not None,
        handoff_artifact_present=bundle.handoff_artifact is not None,
        semantic_evidence_count=len(bundle.semantic_evidence_checksums),
        data_spine_fingerprint_present=bundle.data_spine_fingerprint is not None,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_count=len(blocker_codes) + len(warning_codes),
    )


__all__ = [
    "build_semantic_adjudication_handoff_artifact",
    "verify_semantic_adjudication_handoff_artifact",
    "build_semantic_adjudication_bundle",
    "verify_semantic_adjudication_bundle",
    "summarize_semantic_adjudication_bundle",
]
