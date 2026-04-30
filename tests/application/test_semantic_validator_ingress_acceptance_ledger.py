from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_validator_ingress_acceptance_ledger,
    summarize_semantic_validator_ingress_acceptance_ledger,
    verify_semantic_validator_ingress_acceptance_ledger,
)
from strategy_validator.contracts.semantic import (
    SemanticValidatorHandoffPacketIngressCertificateSummary,
    SemanticValidatorIngressAcceptanceRecord,
)


def _acceptance_record(*, acceptance_id: str = "accept-1", accepted: bool = True) -> SemanticValidatorIngressAcceptanceRecord:
    summary = SemanticValidatorHandoffPacketIngressCertificateSummary(
        certificate_id="cert-1",
        packet_id="packet-1",
        experiment_id="exp-1",
        certificate_verified=True,
        ready_for_validator_ingress=True,
        packet_payload_checksum="packet-sha",
        evidence_payload_checksum="evidence-sha",
        recommended_action="HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR",
        blocker_codes=[],
        warning_codes=[],
        issue_codes=[],
        issue_count=0,
    )
    record = SemanticValidatorIngressAcceptanceRecord(
        acceptance_id=acceptance_id,
        certificate_id="cert-1",
        packet_id="packet-1",
        experiment_id="exp-1",
        evidence_id="evidence-1",
        ready_for_validator_ingress=True,
        accepted_for_validator_adjudication=accepted,
        certificate_payload_checksum="cert-sha",
        packet_payload_checksum="packet-sha",
        evidence_payload_checksum="evidence-sha",
        certificate_summary=summary,
        accepted_by="ci-release-gate",
        acceptance_reason="fixture",
        payload_checksum="pending",
    )
    # The ledger only requires a stable source record checksum here; acceptance-record
    # checksum verification is covered by its dedicated tests.
    return record.model_copy(update={"payload_checksum": "record-sha-" + acceptance_id})


def test_semantic_validator_ingress_acceptance_ledger_chains_records() -> None:
    record = _acceptance_record()
    ledger = build_semantic_validator_ingress_acceptance_ledger([record])

    assert ledger.entry_count == 1
    assert ledger.accepted_entry_count == 1
    assert ledger.entries[0].previous_entry_checksum is None
    assert ledger.entries[0].acceptance_payload_checksum == record.payload_checksum

    report = verify_semantic_validator_ingress_acceptance_ledger(ledger, records=[record])
    assert report.verified is True

    summary = summarize_semantic_validator_ingress_acceptance_ledger(ledger, records=[record])
    assert summary.recommended_action == "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR"


def test_semantic_validator_ingress_acceptance_ledger_detects_duplicate_accepts() -> None:
    first = _acceptance_record(acceptance_id="accept-1")
    second = _acceptance_record(acceptance_id="accept-2")
    ledger = build_semantic_validator_ingress_acceptance_ledger([first, second])

    report = verify_semantic_validator_ingress_acceptance_ledger(ledger, records=[first, second])

    assert report.verified is False
    assert "SEMANTIC_VALIDATOR_INGRESS_ACCEPTANCE_LEDGER_MULTIPLE_ACCEPTS" in report.issue_codes
