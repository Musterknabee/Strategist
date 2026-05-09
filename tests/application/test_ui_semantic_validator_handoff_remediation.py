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
from strategy_validator.application.ui_semantic_validator_handoff_remediation import (
    build_ui_semantic_validator_handoff_remediation_payload,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_terminal_chain(root: Path, *, corrupt_packet_certificate_checksum: bool = False) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="remediation-test")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="remediation-test",
    )

    packet_payload = packet.model_dump(mode="json")
    if corrupt_packet_certificate_checksum:
        packet_payload["certificate_payload_checksum"] = "intentional_bad_certificate_payload_checksum_for_remediation_test"

    _write(root / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(root / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(root / "validator_packet.json", packet_payload)
    _write(root / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))


def test_semantic_validator_handoff_remediation_reports_ready_no_action(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_remediation_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_remediation/v1"
    assert payload["read_plane_only"] is True
    assert payload["mutation_authority"] == "none_read_plane"
    assert payload["summary"]["remediation_count_total"] == 1
    assert payload["summary"]["ready_no_action_count"] == 1
    assert payload["summary"]["action_required_count"] == 0
    row = payload["remediations"][0]
    assert row["remediation_status"] == "READY_NO_ACTION"
    assert row["severity"] == "NONE"
    assert row["operator_action_required"] is False
    assert row["validator_ingress_blocked"] is False
    assert row["recommended_action"] == "REVIEW_READY_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE"
    assert row["remediation_steps"] == []


def test_semantic_validator_handoff_remediation_maps_checksum_break_to_repair_step(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path, corrupt_packet_certificate_checksum=True)

    payload = build_ui_semantic_validator_handoff_remediation_payload(
        search_root=tmp_path,
        require_operator_action=True,
        issue_contains="checksum",
        severity=("CRITICAL",),
    )

    assert payload["summary"]["remediation_count_total"] == 1
    assert payload["summary"]["remediation_count_filtered"] == 1
    assert payload["summary"]["action_required_count"] == 1
    assert payload["summary"]["critical_count"] == 1
    row = payload["remediations"][0]
    assert row["remediation_status"] == "EVIDENCE_REPAIR_REQUIRED"
    assert row["severity"] == "CRITICAL"
    assert row["operator_action_required"] is True
    assert row["validator_ingress_blocked"] is True
    assert "PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH" in row["broken_link_codes"]
    steps = {step["issue_code"]: step for step in row["remediation_steps"]}
    step = steps["PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH"]
    assert step["operator_action"] == "REGENERATE_DOWNSTREAM_ARTIFACT_FROM_CANONICAL_UPSTREAM"
    assert step["mutation_authority"] == "none_read_plane_external_operator_workflow_required"
    assert "CRITICAL_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_remediation_maps_missing_components(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))

    payload = build_ui_semantic_validator_handoff_remediation_payload(
        search_root=tmp_path,
        remediation_status=("LINEAGE_RECONSTRUCTION_REQUIRED",),
    )

    row = payload["remediations"][0]
    assert row["remediation_status"] == "LINEAGE_RECONSTRUCTION_REQUIRED"
    assert row["operator_action_required"] is True
    assert "handoff_certificate" in row["missing_components"]
    assert "validator_packet" in row["missing_components"]
    assert "ingress_certificate" in row["missing_components"]
    actions = {step["operator_action"] for step in row["remediation_steps"]}
    assert "RESTORE_OR_REGENERATE_RELEASE_HANDOFF_CERTIFICATE" in actions
    assert "RESTORE_OR_REGENERATE_VALIDATOR_HANDOFF_PACKET" in actions
    assert "RESTORE_OR_REGENERATE_INGRESS_CERTIFICATE" in actions


def test_semantic_validator_handoff_remediation_route_is_registered(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    client = TestClient(create_app())

    response = client.get(f"/ui/semantic-validator-handoff/remediation?search_root={tmp_path}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_remediation/v1"
    assert payload["summary"]["remediation_count_total"] == 1
