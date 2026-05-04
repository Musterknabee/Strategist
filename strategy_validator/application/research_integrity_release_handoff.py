from __future__ import annotations

from typing import Any

from strategy_validator.application.research_integrity_common import _sha256_payload
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseDecisionLedgerEntry,
    SemanticAdjudicationReleaseDecisionLedgerIssue,
    SemanticAdjudicationReleaseDecisionLedgerVerificationReport,
    SemanticAdjudicationReleaseDecisionLedgerSummary,
    SemanticAdjudicationReleaseHandoffCertificate,
    SemanticAdjudicationReleaseHandoffCertificateIssue,
    SemanticAdjudicationReleaseHandoffCertificateVerificationReport,
    SemanticAdjudicationReleaseHandoffCertificateSummary,
    SemanticReleaseHandoffCertificateEvidenceIssue,
    SemanticReleaseHandoffCertificateEvidenceVerificationReport,
    SemanticReleaseHandoffCertificateEvidenceSummary,
)

def _release_decision_ledger_entry_checksum_payload(
    entry: SemanticAdjudicationReleaseDecisionLedgerEntry,
) -> dict[str, Any]:
    payload = entry.model_dump(mode="json")
    payload.pop("entry_checksum", None)
    return payload


def _release_decision_ledger_checksum_payload(
    ledger: SemanticAdjudicationReleaseDecisionLedger,
) -> dict[str, Any]:
    payload = ledger.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_adjudication_release_decision_ledger(
    records: list[SemanticAdjudicationReleaseDecisionRecord],
) -> SemanticAdjudicationReleaseDecisionLedger:
    """Build a portable append-only ledger over terminal semantic decision records.

    This is deliberately separate from the canonical validator ledger. It gives
    release automation a compact, hash-chained index of final semantic handoff
    decisions so an accepted decision cannot be silently replaced by a later
    blocked or drifted record without changing the ledger checksum.
    """
    if not records:
        base = SemanticAdjudicationReleaseDecisionLedger(
            ledger_id="semantic-release-decision-ledger-empty",
            experiment_id="none",
            entry_count=0,
            accepted_decision_count=0,
            blocked_decision_count=0,
            terminal_recommended_action="NO_SEMANTIC_RELEASE_DECISIONS_RECORDED",
            entries=[],
            payload_checksum="pending",
        )
        checksum = _sha256_payload(_release_decision_ledger_checksum_payload(base))
        return base.model_copy(update={"payload_checksum": checksum})

    experiment_id = records[0].experiment_id
    entries: list[SemanticAdjudicationReleaseDecisionLedgerEntry] = []
    previous: str | None = None
    for index, record in enumerate(records):
        base_entry = SemanticAdjudicationReleaseDecisionLedgerEntry(
            entry_index=index,
            decision_id=record.decision_id,
            capsule_id=record.capsule_id,
            index_id=record.index_id,
            bundle_id=record.bundle_id,
            experiment_id=record.experiment_id,
            decision=record.decision,
            decision_allowed=record.decision_allowed,
            decided_by=record.decided_by,
            decision_payload_checksum=record.payload_checksum,
            previous_entry_checksum=previous,
            entry_checksum="pending",
        )
        entry_checksum = _sha256_payload(_release_decision_ledger_entry_checksum_payload(base_entry))
        entry = base_entry.model_copy(update={"entry_checksum": entry_checksum})
        entries.append(entry)
        previous = entry_checksum

    accepted_count = sum(1 for item in records if item.decision == "ACCEPT_FOR_ADJUDICATION" and item.decision_allowed)
    blocked_count = len(records) - accepted_count
    terminal = records[-1]
    terminal_action = "HAND_OFF_TO_VALIDATOR_ADJUDICATION" if (
        terminal.decision == "ACCEPT_FOR_ADJUDICATION" and terminal.decision_allowed
    ) else "RESPECT_TERMINAL_BLOCK_OR_REBUILD_DECISION"
    base = SemanticAdjudicationReleaseDecisionLedger(
        ledger_id=f"semantic-release-decision-ledger-{experiment_id}-{entries[-1].entry_checksum[:16]}",
        experiment_id=experiment_id,
        entry_count=len(entries),
        accepted_decision_count=accepted_count,
        blocked_decision_count=blocked_count,
        terminal_recommended_action=terminal_action,
        entries=entries,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_release_decision_ledger_checksum_payload(base))
    return base.model_copy(update={"payload_checksum": checksum})


def verify_semantic_adjudication_release_decision_ledger(
    ledger: SemanticAdjudicationReleaseDecisionLedger,
    *,
    records: list[SemanticAdjudicationReleaseDecisionRecord] | None = None,
) -> SemanticAdjudicationReleaseDecisionLedgerVerificationReport:
    """Verify a portable semantic release decision ledger and optional source records."""
    issues: list[SemanticAdjudicationReleaseDecisionLedgerIssue] = []

    def issue(code: str, message: str, *, decision_id: str | None = None, severity: str = "BLOCKER") -> None:
        issues.append(
            SemanticAdjudicationReleaseDecisionLedgerIssue(
                code=code,
                message=message,
                severity=severity,
                decision_id=decision_id,
            )
        )

    observed_checksum = ledger.payload_checksum
    expected_checksum = _sha256_payload(_release_decision_ledger_checksum_payload(ledger))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_CHECKSUM_MISMATCH", "ledger payload checksum does not match canonical payload")
    if ledger.schema_version != "semantic_adjudication_release_decision_ledger/v1":
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic release decision ledger schema version")
    if ledger.entry_count != len(ledger.entries):
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_ENTRY_COUNT_MISMATCH", "ledger entry_count differs from entries length")

    seen_decision_ids: set[str] = set()
    previous: str | None = None
    accepted_count = 0
    for expected_index, entry in enumerate(ledger.entries):
        if entry.entry_index != expected_index:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_SEQUENCE_GAP", "ledger entry_index is not contiguous", decision_id=entry.decision_id)
        if entry.decision_id in seen_decision_ids:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_DUPLICATE_DECISION_ID", "ledger contains duplicate decision_id", decision_id=entry.decision_id)
        seen_decision_ids.add(entry.decision_id)
        if entry.previous_entry_checksum != previous:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_PREVIOUS_HASH_MISMATCH", "ledger previous_entry_checksum does not link to prior entry", decision_id=entry.decision_id)
        expected_entry_checksum = _sha256_payload(_release_decision_ledger_entry_checksum_payload(entry))
        if entry.entry_checksum != expected_entry_checksum:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_ENTRY_CHECKSUM_MISMATCH", "ledger entry checksum does not match canonical entry payload", decision_id=entry.decision_id)
        if entry.experiment_id != ledger.experiment_id:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_EXPERIMENT_MISMATCH", "entry experiment_id differs from ledger experiment_id", decision_id=entry.decision_id)
        if entry.decision == "ACCEPT_FOR_ADJUDICATION" and entry.decision_allowed:
            accepted_count += 1
        previous = entry.entry_checksum

    if ledger.accepted_decision_count != accepted_count:
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_ACCEPT_COUNT_MISMATCH", "accepted_decision_count differs from entries")
    if ledger.blocked_decision_count != ledger.entry_count - accepted_count:
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_BLOCK_COUNT_MISMATCH", "blocked_decision_count differs from entries")
    if accepted_count > 1:
        issue("SEMANTIC_RELEASE_DECISION_LEDGER_MULTIPLE_ACCEPTS", "ledger contains more than one accepted semantic release decision")

    if records is not None:
        rebuilt = build_semantic_adjudication_release_decision_ledger(records)
        if ledger.entries != rebuilt.entries:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_RECORD_DRIFT", "ledger entries differ from supplied source decision records")
        if ledger.payload_checksum != rebuilt.payload_checksum:
            issue("SEMANTIC_RELEASE_DECISION_LEDGER_RECORD_CHECKSUM_DRIFT", "ledger checksum differs from ledger rebuilt from supplied records")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticAdjudicationReleaseDecisionLedgerVerificationReport(
        ledger_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        verified=verified,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        entry_count=len(ledger.entries),
        accepted_decision_count=accepted_count,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ACCEPT_SEMANTIC_RELEASE_DECISION_LEDGER" if verified else "REBUILD_SEMANTIC_RELEASE_DECISION_LEDGER",
    )

def summarize_semantic_adjudication_release_decision_ledger(
    ledger: SemanticAdjudicationReleaseDecisionLedger,
    *,
    verification: SemanticAdjudicationReleaseDecisionLedgerVerificationReport | None = None,
    records: list[SemanticAdjudicationReleaseDecisionRecord] | None = None,
) -> SemanticAdjudicationReleaseDecisionLedgerSummary:
    """Build a compact operator/CI status summary for the terminal decision ledger.

    This is the lightweight release-gate object consumed by automation that
    only needs to know whether the append-only terminal decision history is
    internally consistent and whether its terminal state may hand off to the
    validator adjudication path.
    """
    report = verification or verify_semantic_adjudication_release_decision_ledger(
        ledger,
        records=records,
    )
    terminal = ledger.entries[-1] if ledger.entries else None
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    terminal_accept = bool(
        terminal is not None
        and terminal.decision == "ACCEPT_FOR_ADJUDICATION"
        and terminal.decision_allowed
    )
    if report.verified and terminal_accept and ledger.accepted_decision_count == 1:
        recommended_action = "HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR"
    elif report.verified and terminal is not None:
        recommended_action = "RESPECT_TERMINAL_LEDGER_BLOCK_DECISION"
    elif report.verified:
        recommended_action = "NO_SEMANTIC_RELEASE_DECISION_RECORDED"
    else:
        recommended_action = "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_DECISION_LEDGER"
    return SemanticAdjudicationReleaseDecisionLedgerSummary(
        ledger_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        ledger_verified=report.verified,
        entry_count=ledger.entry_count,
        accepted_decision_count=ledger.accepted_decision_count,
        blocked_decision_count=ledger.blocked_decision_count,
        terminal_decision_id=terminal.decision_id if terminal is not None else None,
        terminal_decision=terminal.decision if terminal is not None else None,
        terminal_decision_allowed=bool(terminal.decision_allowed) if terminal is not None else False,
        terminal_recommended_action=ledger.terminal_recommended_action,
        recommended_action=recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        ledger_issue_codes=report.issue_codes,
        payload_checksum=ledger.payload_checksum,
        issue_count=len(blocker_codes) + len(warning_codes),
    )



def _release_handoff_certificate_checksum_payload(
    certificate: SemanticAdjudicationReleaseHandoffCertificate,
) -> dict[str, Any]:
    payload = certificate.model_dump(mode="json")
    payload.pop("payload_checksum", None)
    return payload


def build_semantic_adjudication_release_handoff_certificate(
    ledger: SemanticAdjudicationReleaseDecisionLedger,
    *,
    records: list[SemanticAdjudicationReleaseDecisionRecord] | None = None,
    issued_by: str = "operator",
    issue_reason: str | None = None,
) -> SemanticAdjudicationReleaseHandoffCertificate:
    """Build the terminal semantic release handoff certificate.

    The certificate intentionally sits outside the canonical validator ledger. It
    is the last portable release artifact proving that the append-only semantic
    decision ledger is verified and that its terminal decision may be handed to
    the validator adjudication authority path.
    """
    summary = summarize_semantic_adjudication_release_decision_ledger(ledger, records=records)
    handoff_allowed = bool(summary.recommended_action == "HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR")
    base = SemanticAdjudicationReleaseHandoffCertificate(
        certificate_id=f"semantic-release-handoff-certificate-{ledger.experiment_id}-{ledger.payload_checksum[:16]}",
        ledger_id=ledger.ledger_id,
        experiment_id=ledger.experiment_id,
        terminal_decision_id=summary.terminal_decision_id,
        terminal_decision=summary.terminal_decision,
        handoff_allowed=handoff_allowed,
        ledger_payload_checksum=ledger.payload_checksum,
        ledger_summary=summary,
        issued_by=issued_by or "operator",
        issue_reason=issue_reason,
        payload_checksum="pending",
    )
    checksum = _sha256_payload(_release_handoff_certificate_checksum_payload(base))
    return base.model_copy(update={"payload_checksum": checksum})


def verify_semantic_adjudication_release_handoff_certificate(
    certificate: SemanticAdjudicationReleaseHandoffCertificate,
    *,
    ledger: SemanticAdjudicationReleaseDecisionLedger | None = None,
    records: list[SemanticAdjudicationReleaseDecisionRecord] | None = None,
) -> SemanticAdjudicationReleaseHandoffCertificateVerificationReport:
    """Verify a terminal semantic release handoff certificate."""
    issues: list[SemanticAdjudicationReleaseHandoffCertificateIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(
            SemanticAdjudicationReleaseHandoffCertificateIssue(
                code=code,
                message=message,
                severity=severity,
            )
        )

    observed_checksum = certificate.payload_checksum
    expected_checksum = _sha256_payload(_release_handoff_certificate_checksum_payload(certificate))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_CHECKSUM_MISMATCH", "certificate payload checksum does not match canonical payload")
    if certificate.schema_version != "semantic_adjudication_release_handoff_certificate/v1":
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic release handoff certificate schema version")
    if certificate.ledger_payload_checksum != certificate.ledger_summary.payload_checksum:
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_LEDGER_SUMMARY_CHECKSUM_MISMATCH", "certificate ledger checksum differs from embedded ledger summary")
    if certificate.handoff_allowed and certificate.ledger_summary.recommended_action != "HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR":
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_ALLOWED_WITH_UNREADY_LEDGER", "certificate allows handoff despite an unready ledger summary")
    if certificate.handoff_allowed and certificate.terminal_decision != "ACCEPT_FOR_ADJUDICATION":
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_ALLOWED_WITH_NON_ACCEPT_TERMINAL_DECISION", "certificate allows handoff without an accepted terminal decision")

    if ledger is not None:
        rebuilt = build_semantic_adjudication_release_handoff_certificate(
            ledger,
            records=records,
            issued_by=certificate.issued_by,
            issue_reason=certificate.issue_reason,
        )
        if certificate.ledger_id != ledger.ledger_id:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_LEDGER_ID_MISMATCH", "certificate ledger_id differs from supplied ledger")
        if certificate.experiment_id != ledger.experiment_id:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EXPERIMENT_MISMATCH", "certificate experiment_id differs from supplied ledger")
        if certificate.ledger_payload_checksum != ledger.payload_checksum:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_LEDGER_CHECKSUM_DRIFT", "certificate ledger checksum differs from supplied ledger")
        if certificate.ledger_summary != rebuilt.ledger_summary:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_SUMMARY_DRIFT", "certificate embedded summary differs from supplied ledger/records")
        if certificate.payload_checksum != rebuilt.payload_checksum:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_REBUILD_CHECKSUM_DRIFT", "certificate checksum differs from certificate rebuilt from supplied ledger")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    allowed = bool(verified and certificate.handoff_allowed)
    return SemanticAdjudicationReleaseHandoffCertificateVerificationReport(
        certificate_id=certificate.certificate_id,
        ledger_id=certificate.ledger_id,
        experiment_id=certificate.experiment_id,
        verified=verified,
        handoff_allowed=allowed,
        expected_payload_checksum=expected_checksum,
        observed_payload_checksum=observed_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="HAND_OFF_TO_VALIDATOR_ADJUDICATION" if allowed else "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE",
    )


def summarize_semantic_adjudication_release_handoff_certificate(
    certificate: SemanticAdjudicationReleaseHandoffCertificate,
    *,
    ledger: SemanticAdjudicationReleaseDecisionLedger | None = None,
    records: list[SemanticAdjudicationReleaseDecisionRecord] | None = None,
    verification: SemanticAdjudicationReleaseHandoffCertificateVerificationReport | None = None,
) -> SemanticAdjudicationReleaseHandoffCertificateSummary:
    """Build the terminal, compact CI/operator handoff status."""
    report = verification or verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records,
    )
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    if report.verified and report.handoff_allowed:
        recommended_action = "HAND_OFF_TO_VALIDATOR_ADJUDICATION"
    elif report.verified:
        recommended_action = "RESPECT_SEMANTIC_RELEASE_HANDOFF_BLOCK"
    else:
        recommended_action = "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE"
    return SemanticAdjudicationReleaseHandoffCertificateSummary(
        certificate_id=certificate.certificate_id,
        ledger_id=certificate.ledger_id,
        experiment_id=certificate.experiment_id,
        certificate_verified=report.verified,
        ledger_verified=certificate.ledger_summary.ledger_verified,
        handoff_allowed=report.handoff_allowed,
        terminal_decision_id=certificate.terminal_decision_id,
        terminal_decision=certificate.terminal_decision,
        recommended_action=recommended_action,
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        certificate_issue_codes=report.issue_codes,
        ledger_payload_checksum=certificate.ledger_payload_checksum,
        certificate_payload_checksum=certificate.payload_checksum,
        issue_count=len(blocker_codes) + len(warning_codes),
    )


_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SCHEMA_VERSION = "semantic_release_handoff_certificate_evidence/v1"
_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SOURCE = "strategy_validator.application.research_integrity.semantic_release_handoff_certificate"


def _is_semantic_release_handoff_certificate_evidence(evidence: Evidence) -> bool:
    return evidence.payload.get("schema_version") == _SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SCHEMA_VERSION


def _semantic_release_handoff_certificate_evidence_checksum_payload(evidence: Evidence) -> dict[str, Any]:
    payload = evidence.model_dump(mode="json")
    payload.pop("checksum", None)
    return payload


def build_semantic_release_handoff_certificate_evidence(
    certificate: SemanticAdjudicationReleaseHandoffCertificate,
) -> Evidence:
    """Wrap a verified semantic release handoff certificate in validator-facing Evidence.

    This is the bridge between the portable semantic release chain and the
    canonical adjudication input stream. The object is still ordinary Evidence;
    it does not grant ledger write authority and it must pass validator gates.
    """
    summary = summarize_semantic_adjudication_release_handoff_certificate(certificate)
    payload = {
        "schema_version": _SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SCHEMA_VERSION,
        "certificate": certificate.model_dump(mode="json"),
        "certificate_summary": summary.model_dump(mode="json"),
        "certificate_id": certificate.certificate_id,
        "certificate_payload_checksum": certificate.payload_checksum,
        "handoff_allowed": bool(summary.handoff_allowed),
    }
    evidence = Evidence(
        evidence_id=f"semantic-release-handoff-certificate-evidence-{certificate.experiment_id}-{certificate.payload_checksum[:16]}",
        experiment_id=certificate.experiment_id,
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        payload=payload,
        source_module=_SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SOURCE,
        checksum="pending",
    )
    checksum = _sha256_payload(_semantic_release_handoff_certificate_evidence_checksum_payload(evidence))
    return evidence.model_copy(update={"checksum": checksum})


def verify_semantic_release_handoff_certificate_evidence(
    evidence: Evidence,
) -> SemanticReleaseHandoffCertificateEvidenceVerificationReport:
    """Verify validator-facing Evidence that wraps a semantic handoff certificate."""
    issues: list[SemanticReleaseHandoffCertificateEvidenceIssue] = []

    def issue(code: str, message: str, *, severity: str = "BLOCKER") -> None:
        issues.append(
            SemanticReleaseHandoffCertificateEvidenceIssue(
                code=code,
                message=message,
                severity=severity,
            )
        )

    observed_checksum = evidence.checksum
    expected_checksum = _sha256_payload(_semantic_release_handoff_certificate_evidence_checksum_payload(evidence))
    if observed_checksum != expected_checksum:
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CHECKSUM_MISMATCH", "evidence checksum does not match canonical payload")
    if evidence.payload.get("schema_version") != _SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SCHEMA_VERSION:
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SCHEMA_VERSION_UNSUPPORTED", "unsupported semantic handoff certificate evidence schema")
    if evidence.source_module != _SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SOURCE:
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_SOURCE_MISMATCH", "semantic handoff certificate evidence source_module is not canonical")

    certificate_id: str | None = None
    certificate_payload_checksum: str | None = None
    certificate_handoff_allowed = False
    raw_certificate = evidence.payload.get("certificate")
    if not isinstance(raw_certificate, dict):
        issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CERTIFICATE_MISSING", "evidence payload is missing embedded certificate")
    else:
        certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(raw_certificate)
        certificate_id = certificate.certificate_id
        certificate_payload_checksum = certificate.payload_checksum
        if certificate.experiment_id != evidence.experiment_id:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_EXPERIMENT_MISMATCH", "embedded certificate experiment_id differs from evidence experiment_id")
        if evidence.payload.get("certificate_id") != certificate.certificate_id:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CERTIFICATE_ID_DRIFT", "payload certificate_id differs from embedded certificate")
        if evidence.payload.get("certificate_payload_checksum") != certificate.payload_checksum:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CERTIFICATE_CHECKSUM_DRIFT", "payload certificate checksum differs from embedded certificate")
        certificate_report = verify_semantic_adjudication_release_handoff_certificate(certificate)
        certificate_handoff_allowed = certificate_report.handoff_allowed
        if not certificate_report.verified:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CERTIFICATE_INVALID", "embedded handoff certificate failed self-verification")
        if evidence.payload.get("handoff_allowed") is not certificate_handoff_allowed:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_HANDOFF_FLAG_DRIFT", "payload handoff_allowed differs from verified certificate status")
        if not certificate_handoff_allowed:
            issue("SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_HANDOFF_NOT_ALLOWED", "embedded certificate does not allow validator handoff")

    verified = not any(item.severity == "BLOCKER" for item in issues)
    return SemanticReleaseHandoffCertificateEvidenceVerificationReport(
        evidence_id=evidence.evidence_id,
        experiment_id=evidence.experiment_id,
        verified=verified,
        handoff_allowed=bool(verified and certificate_handoff_allowed),
        expected_checksum=expected_checksum,
        observed_checksum=observed_checksum,
        certificate_id=certificate_id,
        certificate_payload_checksum=certificate_payload_checksum,
        issue_count=len(issues),
        issue_codes=[item.code for item in issues],
        issues=issues,
        recommended_action="ALLOW_VALIDATOR_SEMANTIC_HANDOFF" if verified and certificate_handoff_allowed else "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_HANDOFF_EVIDENCE",
    )


def summarize_semantic_release_handoff_certificate_evidence(
    evidence: Evidence,
) -> SemanticReleaseHandoffCertificateEvidenceSummary:
    """Return a compact operator/CI status for validator-facing handoff Evidence."""
    report = verify_semantic_release_handoff_certificate_evidence(evidence)
    blocker_codes = [item.code for item in report.issues if item.severity == "BLOCKER"]
    warning_codes = [item.code for item in report.issues if item.severity != "BLOCKER"]
    handoff_ready = bool(report.verified and report.handoff_allowed)
    return SemanticReleaseHandoffCertificateEvidenceSummary(
        evidence_id=report.evidence_id,
        experiment_id=report.experiment_id,
        evidence_verified=report.verified,
        handoff_allowed=report.handoff_allowed,
        certificate_id=report.certificate_id,
        certificate_payload_checksum=report.certificate_payload_checksum,
        evidence_payload_checksum=report.observed_checksum,
        recommended_action="HAND_OFF_CERTIFICATE_EVIDENCE_TO_VALIDATOR" if handoff_ready else "REBUILD_OR_BLOCK_SEMANTIC_HANDOFF_CERTIFICATE_EVIDENCE",
        blocker_codes=blocker_codes,
        warning_codes=warning_codes,
        issue_codes=report.issue_codes,
        issue_count=report.issue_count,
    )


__all__ = [
    "build_semantic_adjudication_release_decision_ledger",
    "verify_semantic_adjudication_release_decision_ledger",
    "summarize_semantic_adjudication_release_decision_ledger",
    "build_semantic_adjudication_release_handoff_certificate",
    "verify_semantic_adjudication_release_handoff_certificate",
    "summarize_semantic_adjudication_release_handoff_certificate",
    "build_semantic_release_handoff_certificate_evidence",
    "verify_semantic_release_handoff_certificate_evidence",
    "summarize_semantic_release_handoff_certificate_evidence",
]
