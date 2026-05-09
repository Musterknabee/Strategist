from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    build_semantic_release_handoff_certificate_evidence,
    build_semantic_validator_handoff_packet,
    build_semantic_validator_handoff_packet_ingress_certificate,
)
from strategy_validator.application.ui_semantic_validator_handoff_decision import (
    build_ui_semantic_validator_handoff_decision_payload,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_terminal_chain(root: Path, *, corrupt_packet_certificate_checksum: bool = False) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="decision-test")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="decision-test",
    )

    packet_payload = packet.model_dump(mode="json")
    if corrupt_packet_certificate_checksum:
        packet_payload["certificate_payload_checksum"] = "intentional_bad_certificate_payload_checksum_for_decision_test"

    _write(root / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(root / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(root / "validator_packet.json", packet_payload)
    _write(root / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))


def test_semantic_validator_handoff_decision_prepares_ready_dossier(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_decision_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_decision/v1"
    assert payload["read_plane_only"] is True
    assert payload["validator_submission_authority"] == "none_read_plane"
    assert payload["summary"]["decision_count_total"] == 1
    assert payload["summary"]["ready_decision_count"] == 1
    assert payload["summary"]["validator_submission_allowed_count"] == 0
    row = payload["decisions"][0]
    assert row["decision_status"] == "READY_FOR_OPERATOR_DECISION_DRAFT"
    assert row["decision_ready"] is True
    assert row["manual_operator_signoff_preparable"] is True
    assert row["manual_operator_signoff_recorded"] is False
    assert row["validator_submission_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["execution_allowed"] is False
    assert row["precondition_pass_count"] == row["precondition_count"]
    assert row["decision_packet"]["recommended_decision"] == "PREPARE_MANUAL_OPERATOR_SIGNOFF_DRAFT"
    assert row["decision_packet"]["human_reviewer_id"] == "<REQUIRED_EXTERNALLY>"


def test_semantic_validator_handoff_decision_blocks_untrusted_checksum_break(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path, corrupt_packet_certificate_checksum=True)

    payload = build_ui_semantic_validator_handoff_decision_payload(
        search_root=tmp_path,
        decision_ready=False,
        issue_contains="checksum",
        trust_banner=("UNTRUSTED",),
    )

    assert payload["summary"]["decision_count_total"] == 1
    assert payload["summary"]["decision_count_filtered"] == 1
    assert payload["summary"]["blocked_decision_count"] == 1
    row = payload["decisions"][0]
    assert row["decision_status"] == "BLOCKED_EVIDENCE_REPAIR_REQUIRED"
    assert row["decision_ready"] is False
    assert row["manual_operator_signoff_preparable"] is False
    assert "PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH" in row["decision_blocker_codes"]
    blocked = {item["precondition_id"] for item in row["decision_preconditions"] if item["status"] == "BLOCK"}
    assert "review_gate_ready" in blocked
    assert "trust_banner_trusted" in blocked
    assert "SEMANTIC_VALIDATOR_HANDOFF_DECISION_BLOCKED_PRESENT" in payload["degraded"]
    assert "UNTRUSTED_SEMANTIC_VALIDATOR_HANDOFF_DECISION_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_decision_blocks_incomplete_lineage(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))

    payload = build_ui_semantic_validator_handoff_decision_payload(
        search_root=tmp_path,
        decision_status=("BLOCKED_LINEAGE_RECONSTRUCTION_REQUIRED",),
    )

    row = payload["decisions"][0]
    assert row["decision_status"] == "BLOCKED_LINEAGE_RECONSTRUCTION_REQUIRED"
    assert row["decision_ready"] is False
    assert row["decision_packet"]["recommended_decision"] == "DO_NOT_SIGN_OFF_REPAIR_REQUIRED"
    assert row["precondition_block_count"] >= 1
    assert any(option["option_id"] == "SUBMIT_TO_VALIDATOR_FROM_THIS_SURFACE" and option["availability"] == "FORBIDDEN" for option in row["decision_options"])


def test_semantic_validator_handoff_decision_route_is_registered(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    with TestClient(create_app()) as client:
        response = client.get(
            "/ui/semantic-validator-handoff/decision",
            params={"search_root": str(tmp_path), "decision_status": "READY_FOR_OPERATOR_DECISION_DRAFT"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_decision/v1"
    assert payload["summary"]["decision_count_returned"] == 1
    assert payload["decisions"][0]["manual_operator_signoff_preparable"] is True
