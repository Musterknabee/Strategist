from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.application.research_integrity_validator_handoff import (
    summarize_semantic_validator_handoff_packet_ingress_certificate,
)
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

def _semantic_validator_ingress_acceptance_record_payload_checksum(
    record: SemanticValidatorIngressAcceptanceRecord,
) -> str:
    payload = record.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return _sha256_payload(payload)


def build_semantic_validator_ingress_acceptance_record(
    certificate: SemanticValidatorHandoffPacketIngressCertificate,
    *,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
    accepted_by: str = "operator",
    acceptance_reason: str = "",
) -> SemanticValidatorIngressAcceptanceRecord:
    """Seal the final operator/CI acceptance of a certified semantic packet for validator adjudication."""
    summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    accepted = summary.recommended_action == "HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR" and summary.ready_for_validator_ingress
    acceptance_id = "semantic-validator-ingress-accept-" + _sha256_payload(
        {
            "certificate_id": certificate.certificate_id,
            "packet_id": certificate.packet_id,
            "experiment_id": certificate.experiment_id,
            "certificate_payload_checksum": certificate.payload_checksum,
            "summary": summary.model_dump(mode="json"),
            "accepted_by": accepted_by,
            "acceptance_reason": acceptance_reason,
        }
    )[:24]
    record = SemanticValidatorIngressAcceptanceRecord(
        acceptance_id=acceptance_id,
        certificate_id=certificate.certificate_id,
        packet_id=certificate.packet_id,
        experiment_id=certificate.experiment_id,
        evidence_id=certificate.evidence_id,
        ready_for_validator_ingress=summary.ready_for_validator_ingress,
        accepted_for_validator_adjudication=accepted,
        certificate_payload_checksum=certificate.payload_checksum,
        packet_payload_checksum=certificate.packet_payload_checksum,
        evidence_payload_checksum=certificate.evidence_payload_checksum,
        certificate_summary=summary,
        accepted_by=accepted_by or "operator",
        acceptance_reason=acceptance_reason or "",
        payload_checksum="pending",
    )
    return record.model_copy(update={"payload_checksum": _semantic_validator_ingress_acceptance_record_payload_checksum(record)})


def verify_semantic_validator_ingress_acceptance_record(
    record: SemanticValidatorIngressAcceptanceRecord,
    *,
    certificate: SemanticValidatorHandoffPacketIngressCertificate | None = None,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorIngressAcceptanceRecordVerificationReport:
    """Verify the sealed final semantic validator-ingress acceptance record."""
    issues: list[SemanticValidatorIngressAcceptanceRecordIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorIngressAcceptanceRecordIssue(code=code, message=message, severity=severity))

    observed = record.payload_checksum
    expected = _semantic_validator_ingress_acceptance_record_payload_checksum(record)
    if observed != expected:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_CHECKSUM_MISMATCH", "acceptance record payload checksum does not match canonical payload")
    if record.schema_version != "semantic_validator_ingress_acceptance_record/v1":
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SCHEMA_UNSUPPORTED", "unsupported validator-ingress acceptance record schema version")
    if record.certificate_id != record.certificate_summary.certificate_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_CERTIFICATE_ID_MISMATCH", "record certificate id differs from embedded certificate summary")
    if record.packet_id != record.certificate_summary.packet_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_PACKET_ID_MISMATCH", "record packet id differs from embedded certificate summary")
    if record.experiment_id != record.certificate_summary.experiment_id:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_EXPERIMENT_MISMATCH", "record experiment id differs from embedded certificate summary")
    if record.packet_payload_checksum != record.certificate_summary.packet_payload_checksum:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_PACKET_CHECKSUM_MISMATCH", "record packet checksum differs from embedded certificate summary")
    if record.evidence_payload_checksum != record.certificate_summary.evidence_payload_checksum:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_EVIDENCE_CHECKSUM_MISMATCH", "record evidence checksum differs from embedded certificate summary")
    if record.ready_for_validator_ingress != record.certificate_summary.ready_for_validator_ingress:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_READY_FLAG_DRIFT", "record ready flag differs from embedded certificate summary")
    if record.accepted_for_validator_adjudication and record.certificate_summary.recommended_action != "HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR":
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_ACCEPTED_WITH_NON_HANDOFF_SUMMARY", "record accepts adjudication but embedded certificate summary does not recommend handoff")
    if record.accepted_for_validator_adjudication and not record.ready_for_validator_ingress:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_ACCEPTED_UNREADY_CERTIFICATE", "record accepts adjudication but the certified packet is not ready for validator ingress")

    if certificate is not None:
        if certificate.certificate_id != record.certificate_id:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SOURCE_CERTIFICATE_ID_MISMATCH", "source certificate id differs from acceptance record")
        if certificate.payload_checksum != record.certificate_payload_checksum:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SOURCE_CERTIFICATE_CHECKSUM_DRIFT", "source certificate checksum differs from acceptance record")
        rebuilt_summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
            certificate,
            packet=packet,
            proposal=proposal,
            require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
        )
        if rebuilt_summary.model_dump(mode="json") != record.certificate_summary.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_RECORD_SUMMARY_DRIFT", "rebuilt certificate summary differs from embedded acceptance summary")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    accepted = bool(record.accepted_for_validator_adjudication and record.ready_for_validator_ingress and verified)
    return SemanticValidatorIngressAcceptanceRecordVerificationReport(
        acceptance_id=record.acceptance_id,
        certificate_id=record.certificate_id,
        packet_id=record.packet_id,
        experiment_id=record.experiment_id,
        verified=verified,
        accepted_for_validator_adjudication=accepted,
        ready_for_validator_ingress=bool(record.ready_for_validator_ingress and verified),
        expected_payload_checksum=expected,
        observed_payload_checksum=observed,
        certificate_payload_checksum=record.certificate_payload_checksum,
        packet_payload_checksum=record.packet_payload_checksum,
        evidence_payload_checksum=record.evidence_payload_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="SUBMIT_ACCEPTED_SEMANTIC_PACKET_TO_VALIDATOR" if accepted else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE",
    )


def summarize_semantic_validator_ingress_acceptance_record(
    record: SemanticValidatorIngressAcceptanceRecord,
    *,
    certificate: SemanticValidatorHandoffPacketIngressCertificate | None = None,
    packet: SemanticValidatorHandoffPacket | None = None,
    proposal: ExperimentManifest | None = None,
    require_packet_evidence_on_proposal: bool = True,
) -> SemanticValidatorIngressAcceptanceRecordSummary:
    """Return a compact operator/CI summary for the terminal validator-ingress acceptance record."""
    report = verify_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=require_packet_evidence_on_proposal,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorIngressAcceptanceRecordSummary(
        acceptance_id=record.acceptance_id,
        certificate_id=record.certificate_id,
        packet_id=record.packet_id,
        experiment_id=record.experiment_id,
        verified=report.verified,
        accepted_for_validator_adjudication=report.accepted_for_validator_adjudication,
        ready_for_validator_ingress=report.ready_for_validator_ingress,
        evidence_id=record.evidence_id,
        certificate_payload_checksum=record.certificate_payload_checksum,
        packet_payload_checksum=record.packet_payload_checksum,
        evidence_payload_checksum=record.evidence_payload_checksum,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


def _semantic_validator_ingress_acceptance_ledger_entry_checksum_payload(
    entry: SemanticValidatorIngressAcceptanceLedgerEntry,
) -> dict[str, Any]:
    payload = entry.model_dump(mode="json")
    payload.pop("entry_checksum", None)
    return payload


def _semantic_validator_ingress_acceptance_ledger_checksum_payload(
    ledger: SemanticValidatorIngressAcceptanceLedger,
) -> dict[str, Any]:
    payload = ledger.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_validator_ingress_acceptance_ledger(
    records: list[SemanticValidatorIngressAcceptanceRecord],
) -> SemanticValidatorIngressAcceptanceLedger:
    """Build a portable append-only ledger over terminal validator-ingress acceptance records."""
    if not records:
        base = SemanticValidatorIngressAcceptanceLedger(
            ledger_id="semantic-validator-ingress-acceptance-ledger-empty",
            experiment_id="none",
            entry_count=0,
            accepted_entry_count=0,
            rejected_entry_count=0,
            terminal_recommended_action="NO_VALIDATOR_INGRESS_ACCEPTANCE_RECORDS_RECORDED",
            entries=[],
            payload_checksum="pending",
        )
        return base.model_copy(
            update={"payload_checksum": _sha256_payload(_semantic_validator_ingress_acceptance_ledger_checksum_payload(base))}
        )

    experiment_id = records[0].experiment_id
    entries: list[SemanticValidatorIngressAcceptanceLedgerEntry] = []
    previous: str | None = None
    for index, record in enumerate(records):
        base_entry = SemanticValidatorIngressAcceptanceLedgerEntry(
            entry_index=index,
            acceptance_id=record.acceptance_id,
            certificate_id=record.certificate_id,
            packet_id=record.packet_id,
            experiment_id=record.experiment_id,
            evidence_id=record.evidence_id,
            accepted_for_validator_adjudication=record.accepted_for_validator_adjudication,
            ready_for_validator_ingress=record.ready_for_validator_ingress,
            accepted_by=record.accepted_by,
            acceptance_payload_checksum=record.payload_checksum,
            previous_entry_checksum=previous,
            entry_checksum="pending",
        )
        entry_checksum = _sha256_payload(_semantic_validator_ingress_acceptance_ledger_entry_checksum_payload(base_entry))
        entry = base_entry.model_copy(update={"entry_checksum": entry_checksum})
        entries.append(entry)
        previous = entry_checksum

    accepted_count = sum(
        1 for item in records if item.accepted_for_validator_adjudication and item.ready_for_validator_ingress
    )
    rejected_count = len(records) - accepted_count
    terminal = records[-1]
    terminal_action = (
        "SUBMIT_ACCEPTED_SEMANTIC_PACKET_TO_VALIDATOR"
        if terminal.accepted_for_validator_adjudication and terminal.ready_for_validator_ingress
        else "RESPECT_TERMINAL_VALIDATOR_INGRESS_BLOCK_OR_REBUILD"
    )
    base = SemanticValidatorIngressAcceptanceLedger(
        ledger_id=f"semantic-validator-ingress-acceptance-ledger-{experiment_id}-{entries[-1].entry_checksum[:16]}",
        experiment_id=experiment_id,
        entry_count=len(entries),
        accepted_entry_count=accepted_count,
        rejected_entry_count=rejected_count,
        terminal_recommended_action=terminal_action,
        entries=entries,
        payload_checksum="pending",
    )
    return base.model_copy(
        update={"payload_checksum": _sha256_payload(_semantic_validator_ingress_acceptance_ledger_checksum_payload(base))}
    )


def verify_semantic_validator_ingress_acceptance_ledger(
    ledger: SemanticValidatorIngressAcceptanceLedger,
    *,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorIngressAcceptanceLedgerVerificationReport:
    """Verify a portable semantic validator-ingress acceptance ledger and optional source records."""
    issues: list[SemanticValidatorIngressAcceptanceLedgerIssue] = []

    def issue(code: str, message: str, *, acceptance_id: str | None = None, severity: str = "BLOCKER") -> None:
        issues.append(
            SemanticValidatorIngressAcceptanceLedgerIssue(
                code=code,
                message=message,
                severity=severity,
                acceptance_id=acceptance_id,
            )
        )

    observed_checksum = ledger.payload_checksum
    expected_checksum = _sha256_payload(_semantic_validator_ingress_acceptance_ledger_checksum_payload(ledger))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_CHECKSUM_MISMATCH", "ledger payload checksum does not match canonical payload")
    if ledger.schema_version != "semantic_validator_ingress_acceptance_ledger/v1":
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_SCHEMA_VERSION_UNSUPPORTED", "unsupported validator-ingress acceptance ledger schema version")
    if ledger.entry_count != len(ledger.entries):
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_ENTRY_COUNT_MISMATCH", "ledger entry_count differs from entries length")

    seen_acceptance_ids: set[str] = set()
    previous: str | None = None
    accepted_count = 0
    for expected_index, entry in enumerate(ledger.entries):
        if entry.entry_index != expected_index:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_SEQUENCE_GAP", "entry_index is not contiguous", acceptance_id=entry.acceptance_id)
        if entry.acceptance_id in seen_acceptance_ids:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_DUPLICATE_ACCEPTANCE_ID", "ledger contains duplicate acceptance_id", acceptance_id=entry.acceptance_id)
        seen_acceptance_ids.add(entry.acceptance_id)
        if entry.previous_entry_checksum != previous:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_PREVIOUS_HASH_MISMATCH", "previous_entry_checksum does not link to prior entry", acceptance_id=entry.acceptance_id)
        expected_entry_checksum = _sha256_payload(_semantic_validator_ingress_acceptance_ledger_entry_checksum_payload(entry))
        if entry.entry_checksum != expected_entry_checksum:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_ENTRY_CHECKSUM_MISMATCH", "entry checksum does not match canonical entry payload", acceptance_id=entry.acceptance_id)
        if entry.experiment_id != ledger.experiment_id:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_EXPERIMENT_MISMATCH", "entry experiment_id differs from ledger experiment_id", acceptance_id=entry.acceptance_id)
        if entry.accepted_for_validator_adjudication and entry.ready_for_validator_ingress:
            accepted_count += 1
        previous = entry.entry_checksum

    if ledger.accepted_entry_count != accepted_count:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_ACCEPT_COUNT_MISMATCH", "accepted_entry_count differs from entries")
    if ledger.rejected_entry_count != ledger.entry_count - accepted_count:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_REJECT_COUNT_MISMATCH", "rejected_entry_count differs from entries")
    if accepted_count > 1:
        issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_MULTIPLE_ACCEPTS", "ledger contains more than one accepted validator-ingress record")

    if records is not None:
        rebuilt = build_semantic_validator_ingress_acceptance_ledger(records)
        if ledger.entries != rebuilt.entries:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_RECORD_DRIFT", "ledger entries differ from supplied source acceptance records")
        if ledger.payload_checksum != rebuilt.payload_checksum:
            issue("SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_RECORD_CHECKSUM_DRIFT", "ledger checksum differs from ledger rebuilt from supplied records")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticValidatorIngressAcceptanceLedgerVerificationReport(
        ledger_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        entry_count=len(ledger.entries),
        accepted_entry_count=accepted_count,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER" if verified else "REBUILD_SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER",
    )


def summarize_semantic_validator_ingress_acceptance_ledger(
    ledger: SemanticValidatorIngressAcceptanceLedger,
    *,
    verification: SemanticValidatorIngressAcceptanceLedgerVerificationReport | None = None,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorIngressAcceptanceLedgerSummary:
    """Build a compact terminal status summary for validator-ingress acceptance ledger state."""
    report = verification or verify_semantic_validator_ingress_acceptance_ledger(ledger, records=records)
    terminal = ledger.entries[-1] if ledger.entries else None
    terminal_ready = bool(
        terminal
        and terminal.accepted_for_validator_adjudication
        and terminal.ready_for_validator_ingress
        and report.verified
        and report.accepted_entry_count == 1
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    recommended_action = (
        "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR"
        if terminal_ready
        else "RESPECT_TERMINAL_VALIDATOR_INGRESS_BLOCK_OR_REBUILD_LEDGER"
    )
    return SemanticValidatorIngressAcceptanceLedgerSummary(
        ledger_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        ledger_verified=report.verified,
        entry_count=ledger.entry_count,
        accepted_entry_count=ledger.accepted_entry_count,
        rejected_entry_count=ledger.rejected_entry_count,
        terminal_acceptance_id=terminal.acceptance_id if terminal else None,
        terminal_packet_id=terminal.packet_id if terminal else None,
        terminal_evidence_id=terminal.evidence_id if terminal else None,
        terminal_accepted_for_validator_adjudication=bool(terminal and terminal.accepted_for_validator_adjudication),
        terminal_ready_for_validator_ingress=bool(terminal and terminal.ready_for_validator_ingress),
        terminal_recommended_action=ledger.terminal_recommended_action,
        recommended_action=recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        ledger_issue_codes=report.issue_codes,
        payload_checksum=ledger.payload_checksum,
        issue_count=report.issue_count,
    )



def _semantic_validator_submission_packet_checksum_payload(
    packet: SemanticValidatorSubmissionPacket,
) -> dict[str, Any]:
    payload = packet.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_validator_submission_packet(
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger,
    *,
    submitted_by: str = "operator",
    submission_reason: str = "",
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacket:
    """Build the terminal packet an operator/CI hands to validator adjudication.

    The packet is intentionally evidence-only: it seals the accepted ingress
    ledger summary and terminal Evidence reference, but it does not write to the
    canonical validator ledger or grant authority.
    """
    summary = summarize_semantic_validator_ingress_acceptance_ledger(
        acceptance_ledger,
        records=records,
    )
    terminal_acceptance_id = summary.terminal_acceptance_id or "none"
    terminal_packet_id = summary.terminal_packet_id or "none"
    terminal_evidence_id = summary.terminal_evidence_id or "none"
    ready = summary.recommended_action == "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR"
    base = SemanticValidatorSubmissionPacket(
        submission_packet_id=f"semantic-validator-submission-packet-{acceptance_ledger.experiment_id}-{acceptance_ledger.payload_checksum[:16]}",
        acceptance_ledger_id=acceptance_ledger.ledger_id,
        experiment_id=acceptance_ledger.experiment_id,
        terminal_acceptance_id=terminal_acceptance_id,
        terminal_packet_id=terminal_packet_id,
        terminal_evidence_id=terminal_evidence_id,
        acceptance_ledger_payload_checksum=acceptance_ledger.payload_checksum,
        acceptance_ledger_summary=summary,
        submitted_by=submitted_by,
        submission_reason=submission_reason,
        ready_for_validator_adjudication=ready,
        payload_checksum="pending",
    )
    return base.model_copy(
        update={"payload_checksum": _sha256_payload(_semantic_validator_submission_packet_checksum_payload(base))}
    )


def verify_semantic_validator_submission_packet(
    submission_packet: SemanticValidatorSubmissionPacket,
    *,
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger | None = None,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacketVerificationReport:
    """Verify a terminal semantic validator submission packet."""
    issues: list[SemanticValidatorSubmissionPacketIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorSubmissionPacketIssue(code=code, message=message, severity=severity))

    observed_checksum = submission_packet.payload_checksum
    expected_checksum = _sha256_payload(_semantic_validator_submission_packet_checksum_payload(submission_packet))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_CHECKSUM_MISMATCH", "submission packet payload checksum does not match canonical payload")
    if submission_packet.schema_version != "semantic_validator_submission_packet/v1":
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic validator submission packet schema version")
    if not submission_packet.ready_for_validator_adjudication:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_NOT_READY", "submission packet is not ready for validator adjudication")
    if submission_packet.acceptance_ledger_summary.recommended_action != "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR":
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_SUMMARY_NOT_HANDOFF_READY", "embedded acceptance-ledger summary is not terminal-handoff ready")
    if submission_packet.acceptance_ledger_summary.payload_checksum != submission_packet.acceptance_ledger_payload_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_CHECKSUM_DRIFT", "embedded acceptance-ledger summary checksum differs from packet ledger checksum")
    if submission_packet.acceptance_ledger_summary.terminal_acceptance_id != submission_packet.terminal_acceptance_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_ACCEPTANCE_ID_DRIFT", "terminal acceptance id differs from embedded ledger summary")
    if submission_packet.acceptance_ledger_summary.terminal_packet_id != submission_packet.terminal_packet_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_PACKET_ID_DRIFT", "terminal packet id differs from embedded ledger summary")
    if submission_packet.acceptance_ledger_summary.terminal_evidence_id != submission_packet.terminal_evidence_id:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_ID_DRIFT", "terminal evidence id differs from embedded ledger summary")

    if acceptance_ledger is not None:
        rebuilt = build_semantic_validator_submission_packet(
            acceptance_ledger,
            submitted_by=submission_packet.submitted_by,
            submission_reason=submission_packet.submission_reason,
            records=records,
        )
        if submission_packet.acceptance_ledger_id != acceptance_ledger.ledger_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_ID_MISMATCH", "packet ledger id differs from supplied acceptance ledger")
        if submission_packet.experiment_id != acceptance_ledger.experiment_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EXPERIMENT_MISMATCH", "packet experiment id differs from supplied acceptance ledger")
        if submission_packet.acceptance_ledger_payload_checksum != acceptance_ledger.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_PAYLOAD_CHECKSUM_DRIFT", "packet ledger checksum differs from supplied acceptance ledger")
        if submission_packet.acceptance_ledger_summary != rebuilt.acceptance_ledger_summary:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_LEDGER_SUMMARY_DRIFT", "embedded acceptance-ledger summary differs from rebuilt summary")
        if submission_packet.payload_checksum != rebuilt.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_REBUILT_CHECKSUM_DRIFT", "packet checksum differs from packet rebuilt from supplied ledger")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    ready = bool(verified and submission_packet.ready_for_validator_adjudication)
    return SemanticValidatorSubmissionPacketVerificationReport(
        submission_packet_id=submission_packet.submission_packet_id,
        acceptance_ledger_id=submission_packet.acceptance_ledger_id,
        experiment_id=submission_packet.experiment_id,
        verified=verified,
        ready_for_validator_adjudication=ready,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="SUBMIT_SEMANTIC_VALIDATOR_PACKET_TO_ADJUDICATION" if ready else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_PACKET",
    )


def summarize_semantic_validator_submission_packet(
    submission_packet: SemanticValidatorSubmissionPacket,
    *,
    acceptance_ledger: SemanticValidatorIngressAcceptanceLedger | None = None,
    records: list[SemanticValidatorIngressAcceptanceRecord] | None = None,
) -> SemanticValidatorSubmissionPacketSummary:
    """Build a compact terminal status summary for validator submission."""
    report = verify_semantic_validator_submission_packet(
        submission_packet,
        acceptance_ledger=acceptance_ledger,
        records=records,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorSubmissionPacketSummary(
        submission_packet_id=submission_packet.submission_packet_id,
        acceptance_ledger_id=submission_packet.acceptance_ledger_id,
        experiment_id=submission_packet.experiment_id,
        submission_verified=report.verified,
        ready_for_validator_adjudication=report.ready_for_validator_adjudication,
        terminal_acceptance_id=submission_packet.terminal_acceptance_id,
        terminal_packet_id=submission_packet.terminal_packet_id,
        terminal_evidence_id=submission_packet.terminal_evidence_id,
        acceptance_ledger_payload_checksum=submission_packet.acceptance_ledger_payload_checksum,
        submission_payload_checksum=submission_packet.payload_checksum,
        submitted_by=submission_packet.submitted_by,
        recommended_action=report.recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION = "semantic_validator_submission_packet_evidence/v1"
_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE = "strategy_validator.application.research_integrity.semantic_validator_submission_packet_evidence"


def build_semantic_validator_submission_packet_evidence(
    submission_packet: SemanticValidatorSubmissionPacket,
) -> Evidence:
    """Wrap the terminal validator submission packet as ordinary validator Evidence.

    This is the final bridge into the normal adjudication evidence stream. It
    carries no write authority; the orchestrator still validates it as evidence
    before any ledger mutation path is reached.
    """
    summary = summarize_semantic_validator_submission_packet(submission_packet)
    payload: dict[str, Any] = {
        "schema_version": _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION,
        "submission_packet": submission_packet.model_dump(mode="json"),
        "submission_packet_summary": summary.model_dump(mode="json"),
        "submission_packet_id": submission_packet.submission_packet_id,
        "submission_packet_payload_checksum": submission_packet.payload_checksum,
        "ready_for_validator_adjudication": summary.ready_for_validator_adjudication,
    }
    checksum = _sha256_payload(payload)
    return Evidence(
        evidence_id=f"semantic-validator-submission-packet-evidence-{submission_packet.experiment_id}-{checksum[:16]}",
        experiment_id=submission_packet.experiment_id,
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        payload=payload,
        source_module=_SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE,
        checksum=checksum,
    )


def verify_semantic_validator_submission_packet_evidence(
    evidence: Evidence,
    *,
    submission_packet: SemanticValidatorSubmissionPacket | None = None,
) -> SemanticValidatorSubmissionPacketEvidenceVerificationReport:
    """Verify Evidence wrapping a terminal semantic validator submission packet."""
    issues: list[SemanticValidatorSubmissionPacketEvidenceIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(SemanticValidatorSubmissionPacketEvidenceIssue(code=code, message=message, severity=severity))

    expected_checksum = _sha256_payload(evidence.payload)
    observed_checksum = evidence.checksum
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_CHECKSUM_MISMATCH", "Evidence checksum does not match canonical payload")
    if evidence.payload.get("schema_version") != _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_VERSION:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SCHEMA_UNSUPPORTED", "unsupported submission-packet Evidence schema")
    if evidence.source_module != _SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE_MISMATCH", "Evidence source_module is not the canonical submission-packet evidence builder")

    packet_id: str | None = None
    packet_checksum: str | None = None
    packet_ready = False
    try:
        embedded_packet = SemanticValidatorSubmissionPacket.model_validate(evidence.payload.get("submission_packet"))
        embedded_summary = SemanticValidatorSubmissionPacketSummary.model_validate(evidence.payload.get("submission_packet_summary"))
    except Exception:
        issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PAYLOAD_INVALID", "Evidence payload does not contain a valid embedded submission packet/summary")
        embedded_packet = None
        embedded_summary = None

    if embedded_packet is not None and embedded_summary is not None:
        packet_id = embedded_packet.submission_packet_id
        packet_checksum = embedded_packet.payload_checksum
        packet_report = verify_semantic_validator_submission_packet(embedded_packet)
        rebuilt_summary = summarize_semantic_validator_submission_packet(embedded_packet)
        packet_ready = bool(packet_report.ready_for_validator_adjudication)
        if evidence.experiment_id != embedded_packet.experiment_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_EXPERIMENT_MISMATCH", "Evidence experiment_id differs from embedded submission packet")
        if evidence.payload.get("submission_packet_id") != embedded_packet.submission_packet_id:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_ID_DRIFT", "payload submission_packet_id differs from embedded packet")
        if evidence.payload.get("submission_packet_payload_checksum") != embedded_packet.payload_checksum:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_CHECKSUM_DRIFT", "payload submission packet checksum differs from embedded packet")
        if evidence.payload.get("ready_for_validator_adjudication") is not packet_ready:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_READY_FLAG_DRIFT", "payload readiness flag differs from verified submission packet")
        if embedded_summary != rebuilt_summary:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SUMMARY_DRIFT", "embedded submission-packet summary differs from rebuilt summary")
        if not packet_report.verified:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_INVALID", "embedded semantic validator submission packet failed verification")
        if not packet_ready:
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_PACKET_NOT_READY", "embedded semantic validator submission packet is not ready for adjudication")
        if submission_packet is not None and submission_packet.model_dump(mode="json") != embedded_packet.model_dump(mode="json"):
            issue("SEMANTIC_VALIDATOR_SUBMISSION_PACKET_EVIDENCE_SOURCE_PACKET_DRIFT", "supplied source submission packet differs from embedded packet")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    ready = bool(verified and packet_ready)
    return SemanticValidatorSubmissionPacketEvidenceVerificationReport(
        evidence_id=evidence.evidence_id,
        experiment_id=evidence.experiment_id,
        verified=verified,
        ready_for_validator_adjudication=ready,
        submission_packet_id=packet_id,
        submission_packet_payload_checksum=packet_checksum,
        expected_checksum=expected_checksum,
        observed_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ALLOW_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE" if ready else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE",
    )


def summarize_semantic_validator_submission_packet_evidence(
    evidence: Evidence,
    *,
    submission_packet: SemanticValidatorSubmissionPacket | None = None,
) -> SemanticValidatorSubmissionPacketEvidenceSummary:
    """Return a compact operator/CI view of validator submission-packet Evidence."""
    report = verify_semantic_validator_submission_packet_evidence(evidence, submission_packet=submission_packet)
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    return SemanticValidatorSubmissionPacketEvidenceSummary(
        evidence_id=report.evidence_id,
        experiment_id=report.experiment_id,
        evidence_verified=report.verified,
        ready_for_validator_adjudication=report.ready_for_validator_adjudication,
        submission_packet_id=report.submission_packet_id,
        submission_packet_payload_checksum=report.submission_packet_payload_checksum,
        evidence_payload_checksum=report.observed_checksum,
        recommended_action="HAND_OFF_SUBMISSION_PACKET_EVIDENCE_TO_VALIDATOR" if report.ready_for_validator_adjudication else "REBUILD_OR_BLOCK_SEMANTIC_VALIDATOR_SUBMISSION_EVIDENCE",
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
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
    "build_semantic_validator_ingress_acceptance_record",
    "verify_semantic_validator_ingress_acceptance_record",
    "summarize_semantic_validator_ingress_acceptance_record",
    "build_semantic_validator_ingress_acceptance_ledger",
    "verify_semantic_validator_ingress_acceptance_ledger",
    "summarize_semantic_validator_ingress_acceptance_ledger",
    "build_semantic_validator_submission_packet",
    "verify_semantic_validator_submission_packet",
    "summarize_semantic_validator_submission_packet",
    "build_semantic_validator_submission_packet_evidence",
    "verify_semantic_validator_submission_packet_evidence",
    "summarize_semantic_validator_submission_packet_evidence",
    "build_semantic_validator_submission_readiness_report",
    "summarize_semantic_validator_submission_readiness",
]
