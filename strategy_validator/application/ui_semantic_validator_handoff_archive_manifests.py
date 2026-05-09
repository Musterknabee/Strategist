"""External archive manifest discovery and normalization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_archive_common import (
    _ARCHIVE_SCHEMA_VERSION,
    _authority_assertion_true,
    _manifest_value,
    _norm,
    _placeholder,
    _read_json,
    _s,
    _sha256,
)


def _is_archive_manifest_candidate(raw: dict[str, Any]) -> bool:
    schema = _s(raw.get("schema_version"))
    if schema == _ARCHIVE_SCHEMA_VERSION:
        return True
    artifact_kind = _norm(raw.get("artifact_kind"))
    if artifact_kind in {
        "SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_MANIFEST",
        "HANDOFF_ARCHIVE_MANIFEST",
        "ARCHIVE_MANIFEST",
    }:
        return True
    return bool(raw.get("archive_packet_digest") or raw.get("source_archive_packet_digest")) and bool(
        raw.get("archive_root") or raw.get("manifest_artifact_count") or raw.get("archived_by")
    )


def _archive_manifest_artifacts(search_root: str | Path | None) -> list[dict[str, Any]]:
    if search_root is None or not str(search_root).strip():
        root = Path.cwd() / "artifacts"
    else:
        root = Path(search_root).expanduser()
        if not root.is_absolute():
            root = (Path.cwd() / root).resolve()
    if not root.exists() or not root.is_dir():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        raw = _read_json(path)
        if raw is None or not _is_archive_manifest_candidate(raw):
            continue
        rows.append(_normalize_archive_manifest(path, raw))
    return rows


def _normalize_archive_manifest(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    issue_codes: list[str] = []
    schema = _s(raw.get("schema_version"))
    manifest_id = _manifest_value(raw, "archive_manifest_id", "manifest_id", "artifact_id") or path.stem
    packet_digest = _manifest_value(raw, "archive_packet_digest", "source_archive_packet_digest", "packet_digest")
    archived_by = _manifest_value(raw, "archived_by", "human_archivist_id", "operator_id")
    created_at_utc = _manifest_value(raw, "created_at_utc", "archived_at_utc", "sealed_at_utc")
    archive_root = _manifest_value(raw, "archive_root", "archive_path")
    artifact_count_raw = raw.get("manifest_artifact_count", raw.get("artifact_count"))
    try:
        artifact_count = int(artifact_count_raw or 0)
    except (TypeError, ValueError):
        artifact_count = 0
        issue_codes.append("ARCHIVE_ARTIFACT_COUNT_INVALID")
    if schema != _ARCHIVE_SCHEMA_VERSION:
        issue_codes.append("ARCHIVE_MANIFEST_SCHEMA_UNRECOGNIZED")
    if not packet_digest:
        issue_codes.append("ARCHIVE_PACKET_DIGEST_MISSING")
    if _placeholder(archived_by):
        issue_codes.append("ARCHIVE_ARCHIVIST_ID_MISSING")
    if not created_at_utc:
        issue_codes.append("ARCHIVE_CREATED_AT_MISSING")
    if _placeholder(archive_root):
        issue_codes.append("ARCHIVE_ROOT_MISSING")
    if artifact_count <= 0:
        issue_codes.append("ARCHIVE_ARTIFACT_COUNT_MISSING")
    escalated = []
    for key in (
        "archive_write_allowed",
        "artifact_mutation_allowed",
        "validator_submission_allowed",
        "adjudication_allowed",
        "promotion_allowed",
        "execution_allowed",
    ):
        if _authority_assertion_true(raw, key):
            escalated.append(key)
    if escalated:
        issue_codes.append("ARCHIVE_AUTHORITY_ESCALATION_CLAIMED")
    verified = not issue_codes
    return {
        "archive_manifest_id": manifest_id,
        "schema_version": schema,
        "artifact_kind": _manifest_value(raw, "artifact_kind") or "semantic_validator_handoff_archive_manifest",
        "artifact_path": str(path.as_posix()),
        "artifact_sha256": _sha256(path),
        "custody_gate_id": _manifest_value(raw, "custody_gate_id", "source_custody_gate_id"),
        "custody_seal_id": _manifest_value(raw, "custody_seal_id", "source_custody_seal_id"),
        "signoff_gate_id": _manifest_value(raw, "signoff_gate_id", "source_signoff_gate_id"),
        "decision_id": _manifest_value(raw, "decision_id", "source_decision_id"),
        "chain_id": _manifest_value(raw, "chain_id", "source_chain_id"),
        "experiment_id": _manifest_value(raw, "experiment_id"),
        "archive_packet_digest": packet_digest,
        "archive_root": archive_root,
        "manifest_artifact_count": artifact_count,
        "archived_by": archived_by,
        "created_at_utc": created_at_utc,
        "trust_banner": _manifest_value(raw, "trust_banner") or "TRUST_RESTRICTED",
        "verified": verified,
        "issue_codes": list(dict.fromkeys(issue_codes)),
        "authority_assertions": {
            "read_plane_only": bool(raw.get("read_plane_only", True)),
            "archive_write_allowed": _authority_assertion_true(raw, "archive_write_allowed"),
            "artifact_mutation_allowed": _authority_assertion_true(raw, "artifact_mutation_allowed"),
            "validator_submission_allowed": _authority_assertion_true(raw, "validator_submission_allowed"),
            "adjudication_allowed": _authority_assertion_true(raw, "adjudication_allowed"),
            "promotion_allowed": _authority_assertion_true(raw, "promotion_allowed"),
            "execution_allowed": _authority_assertion_true(raw, "execution_allowed"),
        },
        "raw_archive_manifest": raw,
    }
