from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from strategy_validator.api.app import create_app
from strategy_validator.application.ui_semantic_validator_handoff_archive import (
    build_ui_semantic_validator_handoff_archive_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody import (
    build_ui_semantic_validator_handoff_custody_payload,
)
from tests.application.test_ui_semantic_validator_handoff_custody import _recorded_signoff, _write_custody_seal
from tests.application.test_ui_semantic_validator_handoff_decision import _write, _write_terminal_chain


def _recorded_custody(root: Path) -> dict[str, object]:
    signoff = _recorded_signoff(root)
    preview = build_ui_semantic_validator_handoff_custody_payload(search_root=root)["custody_gates"][0]
    signoff["custody_packet"] = preview["custody_packet"]
    _write_custody_seal(root, signoff)
    payload = build_ui_semantic_validator_handoff_custody_payload(search_root=root)
    assert payload["summary"]["recorded_custody_seal_count"] == 1
    return payload["custody_gates"][0]


def _write_archive_manifest(root: Path, custody: dict[str, object], *, digest: str | None = None, archived_by: str = "archivist@example.local") -> None:
    packet = custody.get("archive_packet")
    if not isinstance(packet, dict):
        payload = build_ui_semantic_validator_handoff_archive_payload(search_root=root)
        packet = payload["archive_gates"][0]["archive_packet"]
    _write(
        root / "archive_manifest.json",
        {
            "schema_version": "semantic_validator_handoff_archive_manifest/v1",
            "artifact_kind": "semantic_validator_handoff_archive_manifest",
            "archive_manifest_id": "semantic-validator-archive-manifest-test-001",
            "custody_gate_id": custody["custody_gate_id"],
            "custody_seal_id": custody["custody_seal_id"],
            "signoff_gate_id": custody["signoff_gate_id"],
            "decision_id": custody["decision_id"],
            "chain_id": custody["chain_id"],
            "experiment_id": custody["experiment_id"],
            "archive_packet_digest": digest or packet["packet_digest"],
            "archive_root": "artifacts/semantic_validator_handoff/archive/test-001",
            "manifest_artifact_count": 7,
            "archived_by": archived_by,
            "created_at_utc": "2026-05-06T02:00:00+00:00",
            "authority_assertions": {
                "read_plane_only": True,
                "archive_write_allowed": False,
                "artifact_mutation_allowed": False,
                "validator_submission_allowed": False,
                "adjudication_allowed": False,
                "promotion_allowed": False,
                "execution_allowed": False,
            },
        },
    )


def test_semantic_validator_handoff_archive_awaits_external_manifest(tmp_path: Path) -> None:
    _recorded_custody(tmp_path)

    payload = build_ui_semantic_validator_handoff_archive_payload(search_root=tmp_path)

    assert payload["schema_version"] == "ui_semantic_validator_handoff_archive/v1"
    assert payload["read_plane_only"] is True
    assert payload["archive_write_authority"] == "none_read_plane"
    assert payload["summary"]["archive_gate_count_total"] == 1
    assert payload["summary"]["ready_for_archive_manifest_count"] == 1
    row = payload["archive_gates"][0]
    assert row["archive_status"] == "READY_FOR_EXTERNAL_ARCHIVE_MANIFEST"
    assert row["archive_manifest_verified"] is False
    assert row["archive_write_allowed"] is False
    assert row["promotion_allowed"] is False
    assert row["archive_template"]["archive_root"] == "<REQUIRED_EXTERNALLY>"
    assert "EXTERNAL_ARCHIVE_MANIFEST_MISSING" in row["issue_codes"]


def test_semantic_validator_handoff_archive_verifies_matching_manifest(tmp_path: Path) -> None:
    custody = _recorded_custody(tmp_path)
    preview = build_ui_semantic_validator_handoff_archive_payload(search_root=tmp_path)["archive_gates"][0]
    custody["archive_packet"] = preview["archive_packet"]
    _write_archive_manifest(tmp_path, custody)

    payload = build_ui_semantic_validator_handoff_archive_payload(
        search_root=tmp_path,
        archive_status=("ARCHIVE_MANIFEST_VERIFIED",),
        archive_manifest_verified=True,
    )

    assert payload["summary"]["external_archive_manifest_artifact_count"] == 1
    assert payload["summary"]["verified_archive_manifest_count"] == 1
    row = payload["archive_gates"][0]
    assert row["archive_status"] == "ARCHIVE_MANIFEST_VERIFIED"
    assert row["archive_manifest_verified"] is True
    assert row["selected_archive_manifest"]["verified"] is True
    assert row["matched_archive_packet_digest"] == row["archive_packet_digest"]
    assert row["recommended_action"] == "HANDOFF_ARCHIVE_MANIFEST_VERIFIED_RETAIN_FOR_AUDIT"


def test_semantic_validator_handoff_archive_detects_digest_mismatch(tmp_path: Path) -> None:
    custody = _recorded_custody(tmp_path)
    _write_archive_manifest(tmp_path, custody, digest="bad_archive_packet_digest")

    payload = build_ui_semantic_validator_handoff_archive_payload(
        search_root=tmp_path,
        issue_contains="digest",
        archive_manifest_verified=False,
    )

    row = payload["archive_gates"][0]
    assert row["archive_status"] == "ARCHIVE_MANIFEST_DIGEST_MISMATCH"
    assert row["archive_manifest_verified"] is False
    assert "ARCHIVE_PACKET_DIGEST_MISMATCH" in row["issue_codes"]
    assert "INVALID_SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_MANIFEST_PRESENT" in payload["degraded"]


def test_semantic_validator_handoff_archive_blocks_missing_custody(tmp_path: Path) -> None:
    _write_terminal_chain(tmp_path)

    payload = build_ui_semantic_validator_handoff_archive_payload(
        search_root=tmp_path,
        archive_status=("BLOCKED_CUSTODY_NOT_SEALED",),
    )

    row = payload["archive_gates"][0]
    assert row["archive_status"] == "BLOCKED_CUSTODY_NOT_SEALED"
    assert row["archive_manifest_required"] is False
    assert "CUSTODY_SEAL_NOT_RECORDED_FOR_ARCHIVE" in row["issue_codes"]


def test_semantic_validator_handoff_archive_route_is_registered(tmp_path: Path) -> None:
    _recorded_custody(tmp_path)
    with TestClient(create_app()) as client:
        response = client.get(
            "/ui/semantic-validator-handoff/archive",
            params={"search_root": str(tmp_path), "archive_status": "READY_FOR_EXTERNAL_ARCHIVE_MANIFEST"},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["schema_version"] == "ui_semantic_validator_handoff_archive/v1"
    assert payload["summary"]["archive_gate_count_returned"] == 1
