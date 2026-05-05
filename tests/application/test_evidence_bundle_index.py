from __future__ import annotations

import json
from pathlib import Path

from strategy_validator.application.evidence_bundle_index import build_evidence_bundle_index


def _entry(payload: dict[str, object], kind: str) -> dict[str, object]:
    entries = payload.get("entries", [])
    assert isinstance(entries, list)
    match = next(item for item in entries if isinstance(item, dict) and item.get("kind") == kind)
    assert isinstance(match, dict)
    return match


def test_empty_artifact_root_reports_pending_entries(tmp_path: Path) -> None:
    payload = build_evidence_bundle_index(repo_root=tmp_path, artifact_root=tmp_path / "artifacts")
    assert payload["schema_version"] == "evidence_bundle_index/v1"
    assert payload["blockers"] == []
    assert "disclaimers" in payload and len(payload["disclaimers"]) >= 5
    assert _entry(payload, "release_verification_pack")["status"] == "PENDING"
    assert _entry(payload, "paper_replay_manifest")["status"] == "PENDING"


def test_discovers_release_replay_provider_and_branch_audit(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_verification" / "latest"
    provider_root = artifact_root / "provider_paper_loop" / "latest"
    release_root.mkdir(parents=True)
    provider_root.mkdir(parents=True)

    (release_root / "main-release-verification-pack.json").write_text(
        json.dumps({"generated_at_utc": "2026-05-05T00:00:00Z", "status": "PASS"}),
        encoding="utf-8",
    )
    (release_root / "branch-cleanup-audit.json").write_text(
        json.dumps({"generated_at_utc": "2026-05-05T00:01:00Z"}),
        encoding="utf-8",
    )
    (provider_root / "replay_manifest.json").write_text(
        json.dumps({"generated_at_utc": "2026-05-05T00:02:00Z"}),
        encoding="utf-8",
    )
    (provider_root / "provider_evidence_manifest.json").write_text(
        json.dumps({"generated_at_utc": "2026-05-05T00:03:00Z", "evidence_status": "DEGRADED"}),
        encoding="utf-8",
    )

    payload = build_evidence_bundle_index(repo_root=tmp_path, artifact_root=artifact_root)
    assert _entry(payload, "release_verification_pack")["status"] == "PASS"
    assert _entry(payload, "branch_cleanup_audit")["status"] == "OK"
    assert _entry(payload, "paper_replay_manifest")["status"] == "OK"
    assert _entry(payload, "provider_evidence_manifest")["status"] == "DEGRADED"


def test_digest_only_when_include_digests_enabled(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_verification" / "latest"
    release_root.mkdir(parents=True)
    (release_root / "main-release-verification-pack.md").write_text("report", encoding="utf-8")

    without_digests = build_evidence_bundle_index(repo_root=tmp_path, artifact_root=artifact_root, include_digests=False)
    with_digests = build_evidence_bundle_index(repo_root=tmp_path, artifact_root=artifact_root, include_digests=True)
    assert _entry(without_digests, "release_verification_markdown")["sha256"] is None
    assert isinstance(_entry(with_digests, "release_verification_markdown")["sha256"], str)


def test_exists_does_not_imply_verified_integrity(tmp_path: Path) -> None:
    artifact_root = tmp_path / "artifacts"
    release_root = artifact_root / "release_verification" / "latest"
    release_root.mkdir(parents=True)
    (release_root / "repo-handoff.zip").write_bytes(b"zip-bytes")

    payload = build_evidence_bundle_index(repo_root=tmp_path, artifact_root=artifact_root)
    archive_entry = _entry(payload, "repo_archive")
    assert archive_entry["exists"] is True
    assert archive_entry["verified_integrity"] is False
