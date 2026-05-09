from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    build_semantic_release_handoff_certificate_evidence,
    build_semantic_validator_handoff_packet,
    build_semantic_validator_handoff_packet_ingress_certificate,
)
from strategy_validator.application.ui_semantic_validator_handoff_lineage import (
    build_ui_semantic_validator_handoff_lineage_payload,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_terminal_chain(root: Path, *, corrupt_packet_certificate_checksum: bool = False) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="lineage-test")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="lineage-test",
    )

    packet_payload = packet.model_dump(mode="json")
    if corrupt_packet_certificate_checksum:
        packet_payload["certificate_payload_checksum"] = "intentional_bad_certificate_payload_checksum_for_lineage_test"

    _write(root / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(root / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(root / "validator_packet.json", packet_payload)
    _write(root / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))


def test_semantic_validator_handoff_lineage_reports_ready_terminal_chain(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_lineage_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_lineage/v1"
    assert payload["read_plane_only"] is True
    assert payload["validator_submission_authority"] == "none_read_plane"
    assert payload["summary"]["chain_count_total"] == 1
    assert payload["summary"]["ready_chain_count"] == 1
    assert payload["summary"]["broken_chain_count"] == 0
    chain = payload["chains"][0]
    assert chain["status"] == "READY"
    assert chain["complete_chain"] is True
    assert chain["link_integrity_ok"] is True
    assert chain["ready_for_operator_review"] is True
    assert chain["components"]["decision_ledger"]["ledger_id"] == chain["decision_ledger_id"]
    assert chain["components"]["handoff_certificate"]["certificate_id"] == chain["handoff_certificate_id"]
    assert chain["components"]["validator_packet"]["packet_id"] == chain["validator_packet_id"]
    assert chain["components"]["ingress_certificate"]["certificate_id"] == chain["ingress_certificate_id"]


def test_semantic_validator_handoff_lineage_flags_checksum_break_and_filters(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path, corrupt_packet_certificate_checksum=True)

    payload = build_ui_semantic_validator_handoff_lineage_payload(
        search_root=tmp_path,
        require_broken_links=True,
        issue_contains="PACKET_TO_CERTIFICATE",
        chain_status=("BROKEN",),
    )

    assert payload["summary"]["chain_count_total"] == 1
    assert payload["summary"]["chain_count_filtered"] == 1
    assert payload["summary"]["broken_chain_count"] == 1
    chain = payload["chains"][0]
    assert chain["status"] == "BROKEN"
    assert chain["link_integrity_ok"] is False
    assert "PACKET_TO_CERTIFICATE_PAYLOAD_CHECKSUM_MISMATCH" in chain["issue_codes"]
    assert "BROKEN_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_lineage_flags_incomplete_chain(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))

    payload = build_ui_semantic_validator_handoff_lineage_payload(search_root=tmp_path)

    assert payload["summary"]["chain_count_total"] == 1
    chain = payload["chains"][0]
    assert chain["status"] == "INCOMPLETE"
    assert chain["complete_chain"] is False
    assert "MISSING_HANDOFF_CERTIFICATE" in chain["issue_codes"]
    assert "MISSING_VALIDATOR_PACKET" in chain["issue_codes"]
    assert "MISSING_INGRESS_CERTIFICATE" in chain["issue_codes"]
