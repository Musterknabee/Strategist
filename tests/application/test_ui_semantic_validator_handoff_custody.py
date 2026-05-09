from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_semantic_validator_handoff_custody import (
    build_ui_semantic_validator_handoff_custody_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff import (
    build_ui_semantic_validator_handoff_signoff_payload,
)
from tests.application.test_ui_semantic_validator_handoff_decision import _write, _write_terminal_chain
from tests.application.test_ui_semantic_validator_handoff_signoff import _ready_decision, _write_signoff


def _recorded_signoff(root: Path) -> dict[str, object]:
    _write_terminal_chain(root)
    decision = _ready_decision(root)
    _write_signoff(root, decision)
    payload = build_ui_semantic_validator_handoff_signoff_payload(search_root=root)
    assert payload["summary"]["recorded_signoff_count"] == 1
    return payload["signoffs"][0]


def _write_custody_seal(root: Path, signoff: dict[str, object], *, digest: str | None = None, custodian: str = "custodian@example.local") -> None:
    packet = signoff.get("custody_packet")
    if not isinstance(packet, dict):
        payload = build_ui_semantic_validator_handoff_custody_payload(search_root=root)
        packet = payload["custody_gates"][0]["custody_packet"]
    _write(
        root / "custody_seal.json",
        {
            "schema_version": "semantic_validator_handoff_custody_seal/v1",
            "artifact_kind": "semantic_validator_handoff_custody_seal",
            "custody_seal_id": "semantic-validator-custody-seal-test-001",
            "signoff_gate_id": signoff["signoff_gate_id"],
            "signoff_id": signoff["signoff_id"],
            "decision_id": signoff["decision_id"],
            "chain_id": signoff["chain_id"],
            "experiment_id": signoff["experiment_id"],
            "custody_packet_digest": digest or packet["packet_digest"],
            "human_custodian_id": custodian,
            "custody_statement": "I have sealed custody of the semantic validator handoff signoff evidence for archive preparation.",
            "sealed_at_utc": "2026-05-06T01:00:00+00:00",
            "authority_assertions": {
                "read_plane_only": True,
                "custody_seal_write_allowed": False,
                "archive_write_allowed": False,
                "artifact_mutation_allowed": False,
                "validator_submission_allowed": False,
                "adjudication_allowed": False,
                "promotion_allowed": False,
                "execution_allowed": False,
            },
        },
    )


def test_semantic_validator_handoff_custody_awaits_external_seal(tmp_path: Path) -> None:
    _recorded_signoff(tmp_path)

    payload = build_ui_semantic_validator_handoff_custody_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_custody/v1"
    assert payload["read_plane_only"] is True
    assert payload["custody_seal_write_authority"] == "none_read_plane"
    assert payload["summary"]["custody_gate_count_total"] == 1
    assert payload["summary"]["ready_for_custody_seal_count"] == 1
    row = payload["custody_gates"][0]
    assert row["custody_status"] == "READY_FOR_EXTERNAL_CUSTODY_SEAL"
    assert row["custody_seal_recorded"] is False
    assert row["archive_write_allowed"] is False
    assert row["validator_submission_allowed"] is False
    assert row["custody_template"]["human_custodian_id"] == "<REQUIRED_EXTERNALLY>"
    assert "EXTERNAL_CUSTODY_SEAL_MISSING" in row["issue_codes"]


def test_semantic_validator_handoff_custody_records_matching_external_seal(tmp_path: Path) -> None:
    signoff = _recorded_signoff(tmp_path)
    preview = build_ui_semantic_validator_handoff_custody_payload(search_root=tmp_path)["custody_gates"][0]
    signoff["custody_packet"] = preview["custody_packet"]
    _write_custody_seal(tmp_path, signoff)

    payload = build_ui_semantic_validator_handoff_custody_payload(
        search_root=tmp_path,
        custody_status=("CUSTODY_SEAL_RECORDED",),
        custody_seal_recorded=True,
    )

    assert payload["summary"]["external_custody_seal_artifact_count"] == 1
    assert payload["summary"]["recorded_custody_seal_count"] == 1
    row = payload["custody_gates"][0]
    assert row["custody_status"] == "CUSTODY_SEAL_RECORDED"
    assert row["custody_seal_recorded"] is True
    assert row["selected_custody_seal"]["verified"] is True
    assert row["matched_custody_packet_digest"] == row["custody_packet_digest"]
    assert row["recommended_action"] == "HANDOFF_CUSTODY_SEAL_RECORDED_PREPARE_ARCHIVE_MANIFEST"


def test_semantic_validator_handoff_custody_detects_digest_mismatch(tmp_path: Path) -> None:
    signoff = _recorded_signoff(tmp_path)
    _write_custody_seal(tmp_path, signoff, digest="bad_custody_packet_digest")

    payload = build_ui_semantic_validator_handoff_custody_payload(
        search_root=tmp_path,
        issue_contains="digest",
        custody_seal_recorded=False,
    )

    row = payload["custody_gates"][0]
    assert row["custody_status"] == "CUSTODY_SEAL_DIGEST_MISMATCH"
    assert row["custody_seal_recorded"] is False
    assert "CUSTODY_PACKET_DIGEST_MISMATCH" in row["issue_codes"]
    assert "INVALID_SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_SEAL_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_custody_blocks_missing_signoff(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_custody_payload(
        search_root=tmp_path,
        custody_status=("BLOCKED_SIGNOFF_NOT_RECORDED",),
    )

    row = payload["custody_gates"][0]
    assert row["custody_status"] == "BLOCKED_SIGNOFF_NOT_RECORDED"
    assert row["custody_seal_required"] is False
    assert "SIGNOFF_NOT_RECORDED_FOR_CUSTODY" in row["issue_codes"]


def test_semantic_validator_handoff_custody_route_is_registered(tmp_path: Path) -> None:
    _recorded_signoff(tmp_path)
    with TestClient(create_app()) as client:
        response = client.get(
            "/ui/semantic-validator-handoff/custody",
            params={"search_root": str(tmp_path), "custody_status": "READY_FOR_EXTERNAL_CUSTODY_SEAL"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_custody/v1"
    assert payload["summary"]["custody_gate_count_returned"] == 1
