from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.core.enums import EvidenceType
from strategy_validator.contracts.semantic import (
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceRecordIssue,
    SemanticValidatorIngressAcceptanceRecordVerificationReport,
    SemanticValidatorIngressAcceptanceRecordSummary,
    SemanticValidatorIngressAcceptanceLedger,
    SemanticValidatorIngressAcceptanceLedgerEntry,
    SemanticValidatorIngressAcceptanceLedgerIssue,
    SemanticValidatorIngressAcceptanceLedgerVerificationReport,
    SemanticValidatorIngressAcceptanceLedgerSummary,
    SemanticValidatorSubmissionPacket,
    SemanticValidatorSubmissionPacketIssue,
    SemanticValidatorSubmissionPacketVerificationReport,
    SemanticValidatorSubmissionPacketSummary,
    SemanticValidatorSubmissionPacketEvidenceIssue,
    SemanticValidatorSubmissionPacketEvidenceVerificationReport,
    SemanticValidatorSubmissionPacketEvidenceSummary,
    SemanticValidatorSubmissionReadinessIssue,
    SemanticValidatorSubmissionReadinessReport,
    SemanticValidatorSubmissionReadinessSummary,
)
from strategy_validator.application.research_integrity_validator_submission_evidence import (
    _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION,
    _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE,
    verify_semantic_validator_submission_packet_evidence,
)

def _find_semantic_validator_submission_packet_evidence_on_proposal(
    proposal: ExperimentManifest,
) -> Evidence | None:
    """Return the first validator submission-packet Evidence attached to a proposal."""
    for evidence in proposal.evidence_bundle.evidence_items:
        if evidence.source_module == _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE:
            return evidence
        if evidence.payload.get("schema_version") == _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION:
            return evidence
    return None


def build_semantic_validator_submission_readiness_report(
    proposal: ExperimentManifest,
    *,
    submission_packet_evidence: Evidence | None = None,
    require_submission_packet_evidence: bool = True,
) -> SemanticValidatorSubmissionReadinessReport:
    """Run the final end-to-end semantic validator submission readiness check.

    This is intentionally proposal-level: it verifies the terminal validator-facing
    Evidence and confirms that the exact Evidence id/checksum is present on the
    proposal before an operator submits the manifest to the normal adjudicator.
    """
    issues: list[SemanticValidatorSubmissionReadinessIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorSubmissionReadinessIssue(code=code, message=message, severity=severity))

    attached = _find_semantic_validator_submission_packet_evidence_on_proposal(proposal)
    evidence = submission_packet_evidence or attached
    evidence_present = evidence is not None
    evidence_attached = False
    submission_packet_id: str | None = None
    submission_packet_checksum: str | None = None
    evidence_id: str | None = None
    evidence_checksum: str | None = None
    evidence_ready = False

    if evidence is None:
        if require_submission_packet_evidence:
            issue(
                "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_REQUIRED",
                "proposal is expected to carry terminal semantic validator submission-packet Evidence",
            )
        else:
            issue(
                "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_NOT_PRESENT",
                "no terminal semantic validator submission-packet Evidence was supplied or attached",
                severity="WARNING",
            )
    else:
        evidence_id = evidence.evidence_id
        evidence_checksum = evidence.checksum
        report = verify_semantic_validator_submission_packet_evidence(evidence)
        submission_packet_id = report.submission_packet_id
        submission_packet_checksum = report.submission_packet_payload_checksum
        evidence_ready = report.ready_for_validator_adjudication
        if evidence.experiment_id != proposal.experiment_id:
            issue(
                "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_PROPOSAL_EXPERIMENT_MISMATCH",
                "terminal submission-packet Evidence experiment_id differs from proposal experiment_id",
            )
        for item in report.issues:
            issue(item.code, item.message, severity=item.severity)
        for candidate in proposal.evidence_bundle.evidence_items:
            if candidate.evidence_id == evidence.evidence_id and candidate.checksum == evidence.checksum:
                evidence_attached = True
                break
        if not evidence_attached:
            issue(
                "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_NOT_ATTACHED_TO_PROPOSAL",
                "terminal validator submission-packet Evidence is not attached to the proposal evidence bundle",
            )
        if not report.ready_for_validator_adjudication:
            issue(
                "SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE_NOT_READY",
                "terminal validator submission-packet Evidence is not ready for validator adjudication",
            )

    blocker_codes = [item.code for item in issues if item.severity == "BLOCKER"]
    ready = bool(evidence_present and evidence_ready and evidence_attached and not blocker_codes)
    return SemanticValidatorSubmissionReadinessReport(
        experiment_id=proposal.experiment_id,
        ready_for_validator_adjudication=ready,
        submission_evidence_present=evidence_present,
        submission_evidence_id=evidence_id,
        submission_evidence_checksum=evidence_checksum,
        submission_packet_id=submission_packet_id,
        submission_packet_payload_checksum=submission_packet_checksum,
        evidence_attached_to_proposal=evidence_attached,
        require_submission_packet_evidence=require_submission_packet_evidence,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="SUBMIT_PROPOSAL_TO_VALIDATOR_ADJUDICATION" if ready else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_READINESS",
    )


def summarize_semantic_validator_submission_readiness(
    proposal: ExperimentManifest,
    *,
    submission_packet_evidence: Evidence | None = None,
    require_submission_packet_evidence: bool = True,
) -> SemanticValidatorSubmissionReadinessSummary:
    """Return a compact final readiness view for operator/CI gates."""
    report = build_semantic_validator_submission_readiness_report(
        proposal,
        submission_packet_evidence=submission_packet_evidence,
        require_submission_packet_evidence=require_submission_packet_evidence,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorSubmissionReadinessSummary(
        experiment_id=report.experiment_id,
        ready_for_validator_adjudication=report.ready_for_validator_adjudication,
        submission_evidence_present=report.submission_evidence_present,
        evidence_attached_to_proposal=report.evidence_attached_to_proposal,
        submission_evidence_id=report.submission_evidence_id,
        submission_packet_id=report.submission_packet_id,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )

__all__ = [
    "build_semantic_validator_submission_readiness_report",
    "summarize_semantic_validator_submission_readiness",
]
