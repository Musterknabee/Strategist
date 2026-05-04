from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.research_os_export_ops import (
    build_research_os_export_manifest,
    build_ui_research_os_export_latest_payload,
    verify_research_os_export,
)


def _write(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def _seed_required(root: Path) -> None:
    _write(root / "research_os_briefings/latest/research_os_briefing_pack.json", {"schema_version": "research_os_briefing_pack/v1", "briefing_id": "b", "status": "READY"})
    _write(root / "research_os_closure/latest/research_os_closure_manifest.json", {"schema_version": "research_os_closure_manifest/v1", "closure_id": "c", "status": "COMPLETE"})
    _write(root / "research_os_attestation/latest/closure_verification_result.json", {"schema_version": "research_os_closure_verification_result/v1", "export": "verify", "status": "VERIFIED"})
    _write(root / "research_os_attestation/latest/operator_attestation.json", {"schema_version": "research_os_operator_attestation/v1", "attestation_id": "a", "decision": "ACKNOWLEDGED"})


def test_export_bundle_builds_and_verifies(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _seed_required(root)
    _write(root / "shadow_books/latest/shadow_book_manifest.json", {"schema_version": "shadow_book/v1", "status": "ACTIVE"})

    manifest = build_research_os_export_manifest(export_id="demo", artifact_root=root, overwrite=True)

    assert manifest.export_id == "demo"
    assert manifest.status.value in {"READY", "RESTRICTED"}
    assert manifest.archive_sha256
    assert any(f.label == "shadow_book_manifest" and f.present for f in manifest.files)

    result = verify_research_os_export(artifact_root=root)
    assert result.status.value in {"READY", "RESTRICTED"}
    assert result.verified_file_count >= 4


def test_export_missing_required_blocks(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _write(root / "research_os_briefings/latest/research_os_briefing_pack.json", {"schema_version": "research_os_briefing_pack/v1", "status": "READY"})

    manifest = build_research_os_export_manifest(export_id="blocked", artifact_root=root, overwrite=True, include_archive=False)

    assert manifest.status.value == "BLOCKED"
    assert any("REQUIRED_ARTIFACT_NOT_PRESENT" in b for b in manifest.blockers)


def test_export_tamper_detection(tmp_path: Path) -> None:
    root = tmp_path / "artifacts"
    _seed_required(root)
    manifest = build_research_os_export_manifest(export_id="tamper", artifact_root=root, overwrite=True, include_archive=False)
    first_file = next(f for f in manifest.files if f.present and f.bundle_path)
    bundle_file = Path(manifest.bundle_directory) / str(first_file.bundle_path)
    bundle_file.write_text("tampered", encoding="utf-8")

    result = verify_research_os_export(artifact_root=root)

    assert result.status.value == "BLOCKED"
    assert result.changed_file_count == 1


def test_export_read_plane_empty_degraded(tmp_path: Path) -> None:
    payload = build_ui_research_os_export_latest_payload(artifact_root=tmp_path / "artifacts")

    assert payload["schema_version"] == "ui_research_os_export/v1"
    assert "NO_RESEARCH_OS_EXPORT_MANIFEST" in payload["degraded"]
