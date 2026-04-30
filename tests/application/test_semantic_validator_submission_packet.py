from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_validator_ingress_acceptance_ledger,
    build_semantic_validator_submission_packet,
    summarize_semantic_validator_submission_packet,
    verify_semantic_validator_submission_packet,
)
from strategy_validator.contracts.semantic import (
    SemanticValidatorHandoffPacketIngressCertificateSummary,
    SemanticValidatorIngressAcceptanceRecord,
)


def _acceptance_record(*, accepted: bool = True) -> SemanticValidatorIngressAcceptanceRecord:
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
        acceptance_id="accept-1",
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
        payload_checksum="record-sha",
    )
    return record


def test_semantic_validator_submission_packet_seals_accepted_ledger() -> None:
    record = _acceptance_record()
    ledger = build_semantic_validator_ingress_acceptance_ledger([record])
    packet = build_semantic_validator_submission_packet(
        ledger,
        records=[record],
        submitted_by="ci-release-gate",
        submission_reason="ready",
    )

    assert packet.ready_for_validator_adjudication is True
    assert packet.terminal_evidence_id == "evidence-1"
    assert packet.acceptance_ledger_payload_checksum == ledger.payload_checksum

    report = verify_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=[record])
    assert report.verified is True
    assert report.recommended_action == "SUBMIT_SEMANTIC_VALIDATOR_PACKET_TO_ADJUDICATION"

    summary = summarize_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=[record])
    assert summary.ready_for_validator_adjudication is True
    assert summary.terminal_packet_id == "packet-1"


def test_semantic_validator_submission_packet_blocks_unaccepted_ledger() -> None:
    record = _acceptance_record(accepted=False)
    ledger = build_semantic_validator_ingress_acceptance_ledger([record])
    packet = build_semantic_validator_submission_packet(ledger, records=[record])

    report = verify_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=[record])

    assert report.ready_for_validator_adjudication is False
    assert "SEMANTIC_VALIDATOR_SUBMISSION_PACKET_NOT_READY" in report.issue_codes
