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


__all__ = [
    "build_semantic_validator_ingress_acceptance_ledger",
    "verify_semantic_validator_ingress_acceptance_ledger",
    "summarize_semantic_validator_ingress_acceptance_ledger",
]
