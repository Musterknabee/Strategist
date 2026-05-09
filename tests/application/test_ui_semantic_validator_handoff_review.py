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
from strategy_validator.application.ui_semantic_validator_handoff_review import (
    build_ui_semantic_validator_handoff_review_payload,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_terminal_chain(root: Path, *, corrupt_packet_certificate_checksum: bool = False) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="review-test")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="review-test",
    )

    packet_payload = packet.model_dump(mode="json")
    if corrupt_packet_certificate_checksum:
        packet_payload["certificate_payload_checksum"] = "intentional_bad_certificate_payload_checksum_for_review_test"

    _write(root / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(root / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(root / "validator_packet.json", packet_payload)
    _write(root / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))


def test_semantic_validator_handoff_review_allows_clean_ready_chain(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_review_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_review/v1"
    assert payload["read_plane_only"] is True
    assert payload["validator_submission_authority"] == "none_read_plane"
    assert payload["summary"]["review_count_total"] == 1
    assert payload["summary"]["ready_for_operator_review_count"] == 1
    assert payload["summary"]["validator_submission_allowed_count"] == 0
    row = payload["reviews"][0]
    assert row["review_status"] == "READY_FOR_OPERATOR_REVIEW"
    assert row["trust_banner"] == "TRUSTED"
    assert row["operator_review_allowed"] is True
    assert row["validator_submission_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["execution_allowed"] is False
    assert row["review_pass_count"] == row["review_check_count"]
    assert all(check["status"] == "PASS" for check in row["review_checklist"])


def test_semantic_validator_handoff_review_blocks_checksum_break(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path, corrupt_packet_certificate_checksum=True)

    payload = build_ui_semantic_validator_handoff_review_payload(
        search_root=tmp_path,
        operator_review_allowed=False,
        issue_contains="checksum",
        trust_banner=("UNTRUSTED",),
    )

    assert payload["summary"]["review_count_total"] == 1
    assert payload["summary"]["review_count_filtered"] == 1
    assert payload["summary"]["blocked_review_count"] == 1
    assert payload["summary"]["untrusted_count"] == 1
    row = payload["reviews"][0]
    assert row["review_status"] == "EVIDENCE_REPAIR_REQUIRED"
    assert row["trust_banner"] == "UNTRUSTED"
    assert row["operator_review_allowed"] is False
    assert "PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH" in row["review_blocker_codes"]
    blocked_checks = {check["check_id"] for check in row["review_checklist"] if check["status"] == "BLOCK"}
    assert "lineage_integrity_clear" in blocked_checks
    assert "remediation_clear" in blocked_checks
    assert "SEMANTIC_VALIDATOR_HANDOFF_REVIEW_BLOCKED_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_review_blocks_incomplete_lineage(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))

    payload = build_ui_semantic_validator_handoff_review_payload(
        search_root=tmp_path,
        review_status=("LINEAGE_RECONSTRUCTION_REQUIRED",),
    )

    row = payload["reviews"][0]
    assert row["review_status"] == "LINEAGE_RECONSTRUCTION_REQUIRED"
    assert row["operator_review_allowed"] is False
    assert row["component_count_present"] == 1
    blocked_checks = {check["check_id"] for check in row["review_checklist"] if check["status"] == "BLOCK"}
    assert "component_chain_complete" in blocked_checks
    assert "remediation_clear" in blocked_checks


def test_semantic_validator_handoff_review_route_is_registered(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    client = TestClient(create_app())

    response = client.get("/ui/semantic-validator-handoff/review", params={"search_root": str(tmp_path), "review_status": "READY_FOR_OPERATOR_REVIEW"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_review/v1"
    assert payload["summary"]["review_count_returned"] == 1
    assert payload["reviews"][0]["operator_review_allowed"] is True
