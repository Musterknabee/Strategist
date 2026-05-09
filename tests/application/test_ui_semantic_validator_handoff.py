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
from strategy_validator.application.ui_semantic_validator_handoff import (
    build_ui_semantic_validator_handoff_payload,
)
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def test_semantic_validator_handoff_projection_indexes_terminal_handoff_chain(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="test-operator")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="test-operator",
    )

    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(tmp_path / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(tmp_path / "validator_packet.json", packet.model_dump(mode="json"))
    _write(tmp_path / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))

    payload = build_ui_semantic_validator_handoff_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff/v1"
    assert payload["read_plane_only"] is True
    assert payload["validator_submission_authority"] == "none_read_plane"
    assert payload["summary"]["artifact_count_total"] == 4
    assert payload["summary"]["decision_ledger_count"] == 1
    assert payload["summary"]["handoff_certificate_count"] == 1
    assert payload["summary"]["validator_packet_count"] == 1
    assert payload["summary"]["ingress_certificate_count"] == 1
    assert payload["summary"]["validator_ingress_ready_count"] == 1
    assert payload["summary"]["blocked_artifact_count"] == 0
    assert {entry["artifact_kind"] for entry in payload["artifacts"]} == {
        "decision_ledger",
        "handoff_certificate",
        "validator_packet",
        "ingress_certificate",
    }


def test_semantic_validator_handoff_projection_filters_and_invalid_artifacts(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record])
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(tmp_path / "handoff_certificate.json", certificate.model_dump(mode="json"))
    (tmp_path / "semantic_handoff_broken.json").write_text("{not-json", encoding="utf-8")

    payload = build_ui_semantic_validator_handoff_payload(
        search_root=tmp_path,
        artifact_kind=("handoff_certificate",),
        handoff_allowed=True,
        verified=True,
        limit=10,
    )

    assert payload["summary"]["artifact_count_total"] == 2
    assert payload["summary"]["artifact_count_filtered"] == 1
    assert payload["summary"]["invalid_artifact_count"] == 1
    assert payload["artifacts"][0]["artifact_kind"] == "handoff_certificate"
    assert "INVALID_SEMANTIC_VALIDATOR_HANDOFF_ARTIFACTS_PRESENT" in payload["degraded"]
