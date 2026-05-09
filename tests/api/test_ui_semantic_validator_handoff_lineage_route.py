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
from tests.application.test_semantic_release_decision_record import _ready_release_decision_record


def _write(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def test_ui_semantic_validator_handoff_lineage_route_indexes_chain(tmp_path: Path) -> None:
    record = _ready_release_decision_record()
    ledger = build_semantic_adjudication_release_decision_ledger([record])
    certificate = build_semantic_adjudication_release_handoff_certificate(ledger, records=[record], issued_by="api-lineage-test")
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    packet = build_semantic_validator_handoff_packet(evidence)
    ingress_certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        require_packet_evidence_on_proposal=False,
        issued_by="api-lineage-test",
    )
    _write(tmp_path / "decision_ledger.json", ledger.model_dump(mode="json"))
    _write(tmp_path / "handoff_certificate.json", certificate.model_dump(mode="json"))
    _write(tmp_path / "validator_packet.json", packet.model_dump(mode="json"))
    _write(tmp_path / "ingress_certificate.json", ingress_certificate.model_dump(mode="json"))

    response = TestClient(create_app()).get(
        "/ui/semantic-validator-handoff/lineage",
        params={"search_root": str(tmp_path), "chain_status": "READY"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_lineage/v1"
    assert payload["summary"]["chain_count_returned"] == 1
    assert payload["chains"][0]["status"] == "READY"


def test_ui_semantic_validator_handoff_lineage_latest_route_empty_degrades(tmp_path: Path) -> None:
    response = TestClient(create_app()).get(
        "/ui/semantic-validator-handoff/lineage/latest",
        params={"search_root": str(tmp_path)},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_lineage/v1"
    assert payload["read_plane_only"] is True
    assert "NO_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_CHAINS_FOUND" in payload["degraded"]
