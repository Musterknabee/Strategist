from __future__ import annotations

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    summarize_semantic_adjudication_release_handoff_certificate,
    verify_semantic_adjudication_release_handoff_certificate,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def test_semantic_release_handoff_certificate_seals_ready_terminal_decision() -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])

    certificate = build_semantic_adjudication_release_handoff_certificate(
        ledger,
        records=[record],
        issued_by="ci-release-gate",
    )

    report = verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=[record],
    )
    summary = summarize_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=[record],
    )

    assert certificate.handoff_allowed is True
    assert report.verified is True
    assert report.handoff_allowed is True
    assert summary.recommended_action == "HAND_OFF_TO_VALIDATOR_ADJUDICATION"


def test_semantic_release_handoff_certificate_detects_ledger_checksum_drift() -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record])
    drifted = ledger.model_copy(update={"payload_checksum": "0" * 64})

    report = verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=drifted,
        records=[record],
    )

    assert report.verified is False
    assert "SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_LEDGER_CHECKSUM_DRIFT" in report.issue_codes
