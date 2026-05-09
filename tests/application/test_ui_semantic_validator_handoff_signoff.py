from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_semantic_validator_handoff_decision import (
    build_ui_semantic_validator_handoff_decision_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff import (
    build_ui_semantic_validator_handoff_signoff_payload,
)
from tests.application.test_ui_semantic_validator_handoff_decision import _write, _write_terminal_chain


def _ready_decision(root: Path) -> dict[str, object]:
    payload = build_ui_semantic_validator_handoff_decision_payload(search_root=root)
    assert payload["summary"]["ready_decision_count"] == 1
    return payload["decisions"][0]


def _write_signoff(root: Path, decision: dict[str, object], *, digest: str | None = None, reviewer: str = "operator@example.local") -> None:
    packet = decision.get("decision_packet")
    assert isinstance(packet, dict)
    _write(
        root / "operator_signoff.json",
        {
            "schema_version": "semantic_validator_handoff_operator_signoff/v1",
            "artifact_kind": "semantic_validator_handoff_operator_signoff",
            "signoff_id": "semantic-validator-signoff-test-001",
            "decision_id": decision["decision_id"],
            "review_id": decision["review_id"],
            "chain_id": decision["chain_id"],
            "experiment_id": decision["experiment_id"],
            "decision_packet_digest": digest or packet["packet_digest"],
            "human_reviewer_id": reviewer,
            "human_signoff_statement": "I have reviewed the semantic validator handoff decision dossier and approve the external signoff receipt.",
            "signed_at_utc": "2026-05-06T00:00:00+00:00",
            "authority_assertions": {
                "read_plane_only": True,
                "validator_submission_allowed": False,
                "promotion_allowed": False,
                "execution_allowed": False,
                "artifact_mutation_allowed": False,
            },
        },
    )


def test_semantic_validator_handoff_signoff_awaits_external_signoff(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_signoff_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_signoff/v1"
    assert payload["read_plane_only"] is True
    assert payload["signoff_write_authority"] == "none_read_plane"
    assert payload["summary"]["signoff_gate_count_total"] == 1
    assert payload["summary"]["awaiting_signoff_count"] == 1
    assert payload["summary"]["recorded_signoff_count"] == 0
    row = payload["signoffs"][0]
    assert row["signoff_status"] == "AWAITING_OPERATOR_SIGNOFF"
    assert row["signoff_recorded"] is False
    assert row["validator_submission_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["execution_allowed"] is False
    assert row["signoff_template"]["human_reviewer_id"] == "<REQUIRED_EXTERNALLY>"
    assert "OPERATOR_SIGNOFF_MISSING" in row["issue_codes"]


def test_semantic_validator_handoff_signoff_records_matching_external_receipt(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    decision = _ready_decision(tmp_path)
    _write_signoff(tmp_path, decision)

    payload = build_ui_semantic_validator_handoff_signoff_payload(
        search_root=tmp_path,
        signoff_status=("OPERATOR_SIGNOFF_RECORDED",),
        signoff_recorded=True,
    )

    assert payload["summary"]["external_signoff_artifact_count"] == 1
    assert payload["summary"]["recorded_signoff_count"] == 1
    assert payload["summary"]["validator_submission_allowed_count"] == 0
    row = payload["signoffs"][0]
    assert row["signoff_status"] == "OPERATOR_SIGNOFF_RECORDED"
    assert row["signoff_recorded"] is True
    assert row["signoff_valid"] is True
    assert row["selected_signoff"]["verified"] is True
    assert row["matched_signoff_packet_digest"] == row["decision_packet_digest"]
    assert row["recommended_action"] == "HANDOFF_SIGNOFF_RECEIPT_RECORDED_REVIEW_EXTERNAL_SUBMISSION_PATH"


def test_semantic_validator_handoff_signoff_detects_digest_mismatch(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    decision = _ready_decision(tmp_path)
    _write_signoff(tmp_path, decision, digest="bad_decision_packet_digest")

    payload = build_ui_semantic_validator_handoff_signoff_payload(
        search_root=tmp_path,
        issue_contains="digest",
        signoff_recorded=False,
    )

    row = payload["signoffs"][0]
    assert row["signoff_status"] == "SIGNOFF_DIGEST_MISMATCH"
    assert row["signoff_recorded"] is False
    assert "SIGNOFF_DECISION_PACKET_DIGEST_MISMATCH" in row["issue_codes"]
    assert "INVALID_SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_signoff_blocks_non_ready_decision(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path, corrupt_packet_certificate_checksum=True)

    payload = build_ui_semantic_validator_handoff_signoff_payload(
        search_root=tmp_path,
        signoff_status=("BLOCKED_DECISION_NOT_SIGNABLE",),
    )

    row = payload["signoffs"][0]
    assert row["signoff_status"] == "BLOCKED_DECISION_NOT_SIGNABLE"
    assert row["signoff_required"] is False
    assert row["signoff_recorded"] is False
    assert row["decision_ready"] is False
    assert "DECISION_NOT_READY_FOR_OPERATOR_SIGNOFF" in row["issue_codes"]


def test_semantic_validator_handoff_signoff_route_is_registered(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)
    with TestClient(create_app()) as client:
        response = client.get(
            "/ui/semantic-validator-handoff/signoff",
            params={"search_root": str(tmp_path), "signoff_status": "AWAITING_OPERATOR_SIGNOFF"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_signoff/v1"
    assert payload["summary"]["signoff_gate_count_returned"] == 1
    assert payload["signoffs"][0]["signoff_status"] == "AWAITING_OPERATOR_SIGNOFF"
