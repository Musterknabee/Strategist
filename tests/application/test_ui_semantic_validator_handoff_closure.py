from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_semantic_validator_handoff_archive import (
    build_ui_semantic_validator_handoff_archive_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure import (
    build_ui_semantic_validator_handoff_closure_payload,
)
from tests.application.test_ui_semantic_validator_handoff_archive import _recorded_custody, _write_archive_manifest
from tests.application.test_ui_semantic_validator_handoff_decision import _write, _write_terminal_chain


def _verified_archive(root: Path) -> dict[str, object]:
    custody = _recorded_custody(root)
    preview = build_ui_semantic_validator_handoff_archive_payload(search_root=root)["archive_gates"][0]
    custody["archive_packet"] = preview["archive_packet"]
    _write_archive_manifest(root, custody)
    payload = build_ui_semantic_validator_handoff_archive_payload(search_root=root)
    assert payload["summary"]["verified_archive_manifest_count"] == 1
    return payload["archive_gates"][0]


def _write_closure_attestation(
    root: Path,
    archive: dict[str, object],
    *,
    digest: str | None = None,
    closed_by: str = "closer@example.local",
) -> None:
    packet = archive.get("closure_packet")
    if not isinstance(packet, dict):
        payload = build_ui_semantic_validator_handoff_closure_payload(search_root=root)
        packet = payload["closure_gates"][0]["closure_packet"]
    _write(
        root / "closure_attestation.json",
        {
            "schema_version": "semantic_validator_handoff_closure_attestation/v1",
            "artifact_kind": "semantic_validator_handoff_closure_attestation",
            "closure_attestation_id": "semantic-validator-closure-attestation-test-001",
            "archive_gate_id": archive["archive_gate_id"],
            "archive_manifest_id": archive["archive_manifest_id"],
            "custody_gate_id": archive["custody_gate_id"],
            "custody_seal_id": archive["custody_seal_id"],
            "signoff_gate_id": archive["signoff_gate_id"],
            "decision_id": archive["decision_id"],
            "chain_id": archive["chain_id"],
            "experiment_id": archive["experiment_id"],
            "archive_packet_digest": archive["archive_packet_digest"],
            "closure_packet_digest": digest or packet["packet_digest"],
            "final_disposition": "AUDIT_READY_CLOSED",
            "closure_statement": "Archive manifest, custody seal, signoff, and lineage were reviewed for audit retention.",
            "closed_by": closed_by,
            "closed_at_utc": "2026-05-06T03:00:00+00:00",
            "authority_assertions": {
                "read_plane_only": True,
                "closure_write_allowed": False,
                "archive_write_allowed": False,
                "artifact_mutation_allowed": False,
                "validator_submission_allowed": False,
                "adjudication_allowed": False,
                "promotion_allowed": False,
                "execution_allowed": False,
            },
        },
    )


def test_semantic_validator_handoff_closure_awaits_external_attestation(tmp_path: Path) -> None:
    _verified_archive(tmp_path)

    payload = build_ui_semantic_validator_handoff_closure_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_closure/v1"
    assert payload["read_plane_only"] is True
    assert payload["closure_write_authority"] == "none_read_plane"
    assert payload["summary"]["closure_gate_count_total"] == 1
    assert payload["summary"]["ready_for_closure_attestation_count"] == 1
    row = payload["closure_gates"][0]
    assert row["closure_status"] == "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION"
    assert row["closure_attestation_recorded"] is False
    assert row["closure_write_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["closure_template"]["closed_by"] == "<REQUIRED_EXTERNALLY>"
    assert "EXTERNAL_CLOSURE_ATTESTATION_MISSING" in row["issue_codes"]


def test_semantic_validator_handoff_closure_records_matching_attestation(tmp_path: Path) -> None:
    archive = _verified_archive(tmp_path)
    preview = build_ui_semantic_validator_handoff_closure_payload(search_root=tmp_path)["closure_gates"][0]
    archive["closure_packet"] = preview["closure_packet"]
    _write_closure_attestation(tmp_path, archive)

    payload = build_ui_semantic_validator_handoff_closure_payload(
        search_root=tmp_path,
        closure_status=("CLOSURE_ATTESTATION_RECORDED",),
        closure_attestation_recorded=True,
    )

    assert payload["summary"]["external_closure_attestation_artifact_count"] == 1
    assert payload["summary"]["recorded_closure_attestation_count"] == 1
    row = payload["closure_gates"][0]
    assert row["closure_status"] == "CLOSURE_ATTESTATION_RECORDED"
    assert row["closure_attestation_recorded"] is True
    assert row["selected_closure_attestation"]["verified"] is True
    assert row["matched_closure_packet_digest"] == row["closure_packet_digest"]
    assert row["recommended_action"] == "HANDOFF_CLOSURE_RECORDED_RETAIN_AUDIT_TRAIL"


def test_semantic_validator_handoff_closure_detects_digest_mismatch(tmp_path: Path) -> None:
    archive = _verified_archive(tmp_path)
    _write_closure_attestation(tmp_path, archive, digest="bad_closure_packet_digest")

    payload = build_ui_semantic_validator_handoff_closure_payload(
        search_root=tmp_path,
        issue_contains="digest",
        closure_attestation_recorded=False,
    )

    row = payload["closure_gates"][0]
    assert row["closure_status"] == "CLOSURE_ATTESTATION_DIGEST_MISMATCH"
    assert row["closure_attestation_recorded"] is False
    assert "CLOSURE_PACKET_DIGEST_MISMATCH" in row["issue_codes"]
    assert "INVALID_SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_ATTESTATION_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_closure_blocks_missing_archive_verification(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_closure_payload(
        search_root=tmp_path,
        closure_status=("BLOCKED_ARCHIVE_NOT_VERIFIED",),
    )

    row = payload["closure_gates"][0]
    assert row["closure_status"] == "BLOCKED_ARCHIVE_NOT_VERIFIED"
    assert row["closure_attestation_required"] is False
    assert "ARCHIVE_MANIFEST_NOT_VERIFIED_FOR_CLOSURE" in row["issue_codes"]


def test_semantic_validator_handoff_closure_route_is_registered(tmp_path: Path) -> None:
    _verified_archive(tmp_path)
    with TestClient(create_app()) as client:
        response = client.get(
            "/ui/semantic-validator-handoff/closure",
            params={"search_root": str(tmp_path), "closure_status": "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_closure/v1"
    assert payload["summary"]["closure_gate_count_returned"] == 1
