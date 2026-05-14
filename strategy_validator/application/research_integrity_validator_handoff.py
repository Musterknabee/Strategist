from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.application.research_integrity_validator_handoff_ingress_certificate import (
    _validator_handoff_packet_ingress_certificate_payload_checksum,
)
from strategy_validator.application.research_integrity_release_handoff import (
    summarize_semantic_release_handoff_certificate_evidence,
    verify_semantic_release_handoff_certificate_evidence,
)
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleVerificationReport,
    SemanticAdjudicationReleaseHandoffCertificate,
    SemanticAdjudicationReleaseHandoffCertificateVerificationReport,
    SemanticReleaseHandoffCertificateEvidenceVerificationReport,
)
from strategy_validator.contracts.semantic_validator_handoff import (
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIssue,
    SemanticValidatorHandoffPacketSummary,
    SemanticValidatorHandoffPacketVerificationReport,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorHandoffPacketIngressCertificateIssue,
    SemanticValidatorHandoffPacketIngressCertificateSummary,
    SemanticValidatorHandoffPacketIngressCertificateVerificationReport,
    SemanticValidatorHandoffPacketIngressIssue,
    SemanticValidatorHandoffPacketIngressReport,
    SemanticValidatorHandoffPacketIngressSummary,
)


_SEMANTIC_VALIDATOR_HANDOFF_PACKET_SCHEMA_VERSION = "semantic_validator_handoff_packet/v1"


def _semantic_validator_handoff_packet_checksum_payload(packet: SemanticValidatorHandoffPacket) -> dict[str, Any]:
    payload = packet.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_validator_handoff_packet(
    evidence: Evidence,
) -> SemanticValidatorHandoffPacket:
    """Build a portable, checksummed packet for validator ingress handoff Evidence."""
    summary = summarize_semantic_release_handoff_certificate_evidence(evidence)
    packet = SemanticValidatorHandoffPacket(
        packet_id=f"semantic-validator-handoff-packet-{evidence.experiment_id}-{evidence.checksum[:16]}",
        experiment_id=evidence.experiment_id,
        evidence_id=evidence.evidence_id,
        evidence_payload_checksum=evidence.checksum,
        certificate_id=summary.certificate_id,
        certificate_payload_checksum=summary.certificate_payload_checksum,
        handoff_allowed=summary.handoff_allowed,
        evidence=evidence.model_dump(mode="json"),
        evidence_summary=summary,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_semantic_validator_handoff_packet_checksum_payload(packet))
    return packet.model_copy(update={"payload_checksum": checksum})


def verify_semantic_validator_handoff_packet(
    packet: SemanticValidatorHandoffPacket,
    *,
    evidence: Evidence | None = None,
) -> SemanticValidatorHandoffPacketVerificationReport:
    """Verify the portable validator handoff packet and optional source Evidence."""
    issues: list[SemanticValidatorHandoffPacketIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorHandoffPacketIssue(code=code, message=message, severity=severity))

    expected_checksum = _sha256_payload(_semantic_validator_handoff_packet_checksum_payload(packet))
    observed_checksum = packet.payload_checksum
    if packet.schema_version != _SEMANTIC_VALIDATOR_HANDOFF_PACKET_SCHEMA_VERSION:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_SCHEMA_VERSION_UNSUPPORTED", "unsupported validator handoff packet schema")
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_CHECKSUM_MISMATCH", "packet checksum does not match canonical payload")

    embedded_evidence = Evidence.model_validate(packet.evidence)
    evidence_report = verify_semantic_release_handoff_certificate_evidence(embedded_evidence)
    rebuilt_summary = summarize_semantic_release_handoff_certificate_evidence(embedded_evidence)
    if not evidence_report.verified:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_INVALID", "embedded validator handoff Evidence failed verification")
    if packet.experiment_id != embedded_evidence.experiment_id:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_EXPERIMENT_MISMATCH", "packet experiment_id differs from embedded Evidence")
    if packet.evidence_id != embedded_evidence.evidence_id:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_ID_DRIFT", "packet evidence_id differs from embedded Evidence")
    if packet.evidence_payload_checksum != embedded_evidence.checksum:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_CHECKSUM_DRIFT", "packet evidence checksum differs from embedded Evidence")
    if packet.certificate_id != evidence_report.certificate_id:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_CERTIFICATE_ID_DRIFT", "packet certificate_id differs from verified Evidence")
    if packet.certificate_payload_checksum != evidence_report.certificate_payload_checksum:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_CERTIFICATE_CHECKSUM_DRIFT", "packet certificate checksum differs from verified Evidence")
    if packet.handoff_allowed is not evidence_report.handoff_allowed:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_HANDOFF_FLAG_DRIFT", "packet handoff_allowed differs from verified Evidence")
    if packet.evidence_summary != rebuilt_summary:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_SUMMARY_DRIFT", "packet embedded Evidence summary differs from rebuilt summary")
    if not evidence_report.handoff_allowed:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_HANDOFF_NOT_ALLOWED", "embedded Evidence does not allow validator handoff")

    if evidence is not None:
        if evidence.model_dump(mode="json") != embedded_evidence.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_SOURCE_EVIDENCE_DRIFT", "supplied source Evidence differs from packet embedded Evidence")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    handoff_allowed = bool(verified and evidence_report.handoff_allowed and packet.handoff_allowed)
    return SemanticValidatorHandoffPacketVerificationReport(
        packet_id=packet.packet_id,
        experiment_id=packet.experiment_id,
        verified=verified,
        handoff_allowed=handoff_allowed,
        evidence_id=packet.evidence_id,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        evidence_payload_checksum=packet.evidence_payload_checksum,
        certificate_id=packet.certificate_id,
        certificate_payload_checksum=packet.certificate_payload_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="HAND_OFF_PACKET_TO_VALIDATOR" if handoff_allowed else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_HANDOFF_PACKET",
    )


def summarize_semantic_validator_handoff_packet(
    packet: SemanticValidatorHandoffPacket,
    *,
    evidence: Evidence | None = None,
) -> SemanticValidatorHandoffPacketSummary:
    """Return the smallest CI/operator view of a validator handoff packet."""
    report = verify_semantic_validator_handoff_packet(packet, evidence=evidence)
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorHandoffPacketSummary(
        packet_id=packet.packet_id,
        experiment_id=packet.experiment_id,
        packet_verified=report.verified,
        evidence_verified=not any(code == "SEMANTIC_VALIDATOR_HANDOFF_PACKET_EVIDENCE_INVALID" for code in report.issue_codes),
        handoff_allowed=report.handoff_allowed,
        evidence_id=packet.evidence_id,
        certificate_id=packet.certificate_id,
        packet_payload_checksum=packet.payload_checksum,
        evidence_payload_checksum=packet.evidence_payload_checksum,
        recommended_action="HAND_OFF_PACKET_TO_VALIDATOR" if report.verified and report.handoff_allowed else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_HANDOFF_PACKET",
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


def build_semantic_validator_handoff_packet_ingress_report(
    packet: SemanticValidatorHandoffPacket,
    *,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorHandoffPacketIngressReport:
    """Pre-adjudication gate report for a semantic validator handoff packet.

    The report is intentionally read-only. It verifies the portable packet,
    verifies the embedded validator-facing Evidence, and optionally proves the
    same Evidence already exists on the proposal that will be handed to the
    validator. It does not grant ledger authority and does not mutate the
    proposal.
    """
    issues: list[SemanticValidatorHandoffPacketIngressIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorHandoffPacketIngressIssue(code=code, message=message, severity=severity))

    packet_report = verify_semantic_validator_handoff_packet(packet)
    embedded_evidence = Evidence.model_validate(packet.evidence)
    evidence_report = verify_semantic_release_handoff_certificate_evidence(embedded_evidence)

    if not packet_report.verified:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_PACKET_INVALID", "validator handoff packet failed verification")
    if not packet_report.handoff_allowed:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_HANDOFF_NOT_ALLOWED", "validator handoff packet does not allow handoff")
    if not evidence_report.verified:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_EVIDENCE_INVALID", "embedded validator handoff Evidence failed verification")
    if not evidence_report.handoff_allowed:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_EVIDENCE_HANDOFF_NOT_ALLOWED", "embedded Evidence does not allow handoff")

    proposal_experiment_id: str | None = None
    evidence_present = False
    if proposal is not None:
        proposal_experiment_id = proposal.experiment_id
        if proposal.experiment_id != packet.experiment_id:
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_EXPERIMENT_MISMATCH", "proposal experiment_id differs from packet experiment_id")
        for ev in proposal.evidence_bundle.evidence_items:
            if ev.evidence_id == embedded_evidence.evidence_id and ev.checksum == embedded_evidence.checksum:
                evidence_present = True
                break
        if require_packet_evidence_on_proposal and not evidence_present:
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_EVIDENCE_NOT_ON_PROPOSAL", "packet Evidence is not present on the proposal evidence bundle")
    elif require_packet_evidence_on_proposal:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_PROPOSAL_REQUIRED", "proposal is required to prove packet Evidence is attached before adjudication")

    ready = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticValidatorHandoffPacketIngressReport(
        packet_id=packet.packet_id,
        experiment_id=packet.experiment_id,
        proposal_experiment_id=proposal_experiment_id,
        packet_verified=packet_report.verified,
        evidence_verified=evidence_report.verified,
        handoff_allowed=bool(packet_report.handoff_allowed and evidence_report.handoff_allowed),
        evidence_present_on_proposal=evidence_present,
        ready_for_validator_ingress=ready,
        evidence_id=packet.evidence_id,
        evidence_payload_checksum=packet.evidence_payload_checksum,
        packet_payload_checksum=packet.payload_checksum,
        certificate_id=packet.certificate_id,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="HAND_OFF_PACKET_EVIDENCE_TO_VALIDATOR" if ready else "REBUILD_OR_BLOCK_VALIDATOR_HANDOFF_PACKET_INGRESS",
    )


def summarize_semantic_validator_handoff_packet_ingress(
    packet: SemanticValidatorHandoffPacket,
    *,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorHandoffPacketIngressSummary:
    """Return a compact CI/operator summary for validator-ingress packet readiness."""
    report = build_semantic_validator_handoff_packet_ingress_report(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorHandoffPacketIngressSummary(
        packet_id=report.packet_id,
        experiment_id=report.experiment_id,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        packet_verified=report.packet_verified,
        evidence_verified=report.evidence_verified,
        handoff_allowed=report.handoff_allowed,
        evidence_present_on_proposal=report.evidence_present_on_proposal,
        evidence_id=report.evidence_id,
        certificate_id=report.certificate_id,
        packet_payload_checksum=report.packet_payload_checksum,
        evidence_payload_checksum=report.evidence_payload_checksum,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


def build_semantic_validator_handoff_packet_ingress_certificate(
    packet: SemanticValidatorHandoffPacket,
    *,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
    issued_by: str = "operator",
    issue_reason: str = "",
) -> SemanticValidatorHandoffPacketIngressCertificate:
    """Seal the pre-adjudication validator-ingress result as a portable certificate."""
    report = build_semantic_validator_handoff_packet_ingress_report(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    certificate_id = "semantic-validator-ingress-cert-" + _sha256_payload(
        {
            "packet_id": packet.packet_id,
            "experiment_id": packet.experiment_id,
            "packet_payload_checksum": packet.payload_checksum,
            "report": report.model_dump(mode="json"),
            "issued_by": issued_by,
            "issue_reason": issue_reason,
        }
    )[:24]
    cert = SemanticValidatorHandoffPacketIngressCertificate(
        certificate_id=certificate_id,
        packet_id=packet.packet_id,
        experiment_id=packet.experiment_id,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        evidence_id=packet.evidence_id,
        packet_payload_checksum=packet.payload_checksum,
        evidence_payload_checksum=packet.evidence_payload_checksum,
        ingress_report=report,
        issued_by=issued_by or "operator",
        issue_reason=issue_reason or "",
        payload_checksum="pending",
    )
    return cert.model_copy(update={"payload_checksum": _validator_handoff_packet_ingress_certificate_payload_checksum(cert)})


def verify_semantic_validator_handoff_packet_ingress_certificate(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
    *,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorHandoffPacketIngressCertificateVerificationReport:
    """Verify a sealed validator-ingress packet certificate against optional source inputs."""
    issues: list[SemanticValidatorHandoffPacketIngressCertificateIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorHandoffPacketIngressCertificateIssue(code=code, message=message, severity=severity))

    observed = certificate.payload_checksum
    expected = _validator_handoff_packet_ingress_certificate_payload_checksum(certificate)
    if observed != expected:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_CHECKSUM_MISMATCH", "certificate payload checksum does not match canonical payload")
    if certificate.schema_version != "semantic_validator_handoff_packet_ingress_certificate/v1":
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_SCHEMA_UNSUPPORTED", "unsupported validator-ingress certificate schema version")
    if certificate.packet_id != certificate.ingress_report.packet_id:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_PACKET_ID_MISMATCH", "certificate packet_id differs from embedded ingress report")
    if certificate.experiment_id != certificate.ingress_report.experiment_id:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_EXPERIMENT_MISMATCH", "certificate experiment_id differs from embedded ingress report")
    if certificate.packet_payload_checksum != certificate.ingress_report.packet_payload_checksum:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_PACKET_CHECKSUM_MISMATCH", "certificate packet checksum differs from embedded ingress report")
    if certificate.evidence_payload_checksum != certificate.ingress_report.evidence_payload_checksum:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_EVIDENCE_CHECKSUM_MISMATCH", "certificate evidence checksum differs from embedded ingress report")
    if certificate.ready_for_validator_ingress != certificate.ingress_report.ready_for_validator_ingress:
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_READY_FLAG_DRIFT", "certificate ready flag differs from embedded ingress report")
    if certificate.ready_for_validator_ingress and certificate.ingress_report.recommended_action != "HAND_OFF_PACKET_EVIDENCE_TO_VALIDATOR":
        issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_READY_WITH_NON_HANDOFF_REPORT", "certificate is ready but embedded report does not recommend handoff")

    if packet is not None:
        if packet.packet_id != certificate.packet_id:
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_SOURCE_PACKET_ID_MISMATCH", "source packet id differs from certificate")
        if packet.payload_checksum != certificate.packet_payload_checksum:
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_SOURCE_PACKET_CHECKSUM_DRIFT", "source packet checksum differs from certificate")
        rebuilt = build_semantic_validator_handoff_packet_ingress_report(
            packet,
            proposal=proposal,
            require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
        )
        if rebuilt.model_dump(mode="json") != certificate.ingress_report.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE_REPORT_DRIFT", "rebuilt ingress report differs from embedded certificate report")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticValidatorHandoffPacketIngressCertificateVerificationReport(
        certificate_id=certificate.certificate_id,
        packet_id=certificate.packet_id,
        experiment_id=certificate.experiment_id,
        verified=verified,
        ready_for_validator_ingress=bool(certificate.ready_for_validator_ingress and verified),
        expected_payload_checksum=expected,
        observed_payload_checksum=observed,
        packet_payload_checksum=certificate.packet_payload_checksum,
        evidence_payload_checksum=certificate.evidence_payload_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR" if verified and certificate.ready_for_validator_ingress else "REBUILD_OR_BLOCK_VALIDATOR_HANDOFF_PACKET_INGRESS_CERTIFICATE",
    )


def summarize_semantic_validator_handoff_packet_ingress_certificate(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
    *,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorHandoffPacketIngressCertificateSummary:
    """Return a compact operator/CI summary for a validator-ingress certificate."""
    report = verify_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorHandoffPacketIngressCertificateSummary(
        certificate_id=certificate.certificate_id,
        packet_id=certificate.packet_id,
        experiment_id=certificate.experiment_id,
        certificate_verified=report.verified,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        packet_payload_checksum=certificate.packet_payload_checksum,
        evidence_payload_checksum=certificate.evidence_payload_checksum,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )
