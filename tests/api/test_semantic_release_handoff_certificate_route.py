from __future__ import annotations

from strategy_validator.api.routes.research_release import (
    SemanticAdjudicationReleaseHandoffCertificateRequest,
    SemanticAdjudicationReleaseHandoffCertificateVerificationRequest,
    semantic_adjudication_release_handoff_certificate,
    semantic_adjudication_release_handoff_certificate_summary,
    semantic_adjudication_release_handoff_certificate_verify,
)
from strategy_validator.application.research_integrity import build_semantic_adjudication_release_decision_ledger
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def test_semantic_release_handoff_certificate_route_round_trip() -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate_payload = semantic_adjudication_release_handoff_certificate(
        SemanticAdjudicationReleaseHandoffCertificateRequest(
            decision_ledger=ledger.model_dump(mode="json"),
            decision_records=[record.model_dump(mode="json")],
            issued_by="api-test",
        )
    )

    verification_payload = semantic_adjudication_release_handoff_certificate_verify(
        SemanticAdjudicationReleaseHandoffCertificateVerificationRequest(
            certificate=certificate_payload,
            decision_ledger=ledger.model_dump(mode="json"),
            decision_records=[record.model_dump(mode="json")],
        )
    )
    summary_payload = semantic_adjudication_release_handoff_certificate_summary(
        SemanticAdjudicationReleaseHandoffCertificateVerificationRequest(
            certificate=certificate_payload,
            decision_ledger=ledger.model_dump(mode="json"),
            decision_records=[record.model_dump(mode="json")],
        )
    )

    assert verification_payload["verified"] is True
    assert summary_payload["recommended_action"] == "HAND_OFF_TO_VALIDATOR_ADJUDICATION"
