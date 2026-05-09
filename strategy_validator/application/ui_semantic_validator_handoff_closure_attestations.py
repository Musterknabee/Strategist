"""Closure attestation artifact discovery and normalization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_closure_common import (
    _CLOSURE_SCHEMA_VERSION,
    _authority_assertion_true,
    _closure_value,
    _norm,
    _placeholder,
    _read_json,
    _s,
    _sha256,
)


def _is_closure_attestation_candidate(raw: dict[str, Any]) -> bool:
    schema = _s(raw.get("schema_version"))
    if schema == _CLOSURE_SCHEMA_VERSION:
        return True
    artifact_kind = _norm(raw.get("artifact_kind"))
    if artifact_kind in {
        "SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_ATTESTATION",
        "HANDOFF_CLOSURE_ATTESTATION",
        "CLOSURE_ATTESTATION",
        "HANDOFF_CLOSEOUT",
    }:
        return True
    return bool(raw.get("closure_packet_digest") or raw.get("source_closure_packet_digest")) and bool(
        raw.get("closed_by") or raw.get("closure_statement") or raw.get("final_disposition")
    )

def _closure_attestation_artifacts(search_root: str | Path | None) -> list[dict[str, Any]]:
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
        if raw is None or not _is_closure_attestation_candidate(raw):
            continue
        rows.append(_normalize_closure_attestation(path, raw))
    return rows

def _normalize_closure_attestation(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    issue_codes: list[str] = []
    schema = _s(raw.get("schema_version"))
    attestation_id = _closure_value(raw, "closure_attestation_id", "closeout_id", "artifact_id") or path.stem
    packet_digest = _closure_value(raw, "closure_packet_digest", "source_closure_packet_digest", "packet_digest")
    closed_by = _closure_value(raw, "closed_by", "human_closer_id", "operator_id")
    closed_at_utc = _closure_value(raw, "closed_at_utc", "closure_at_utc", "attested_at_utc")
    final_disposition = _closure_value(raw, "final_disposition", "closure_disposition", "disposition")
    closure_statement = _closure_value(raw, "closure_statement", "attestation_statement", "statement")
    if schema != _CLOSURE_SCHEMA_VERSION:
        issue_codes.append("CLOSURE_ATTESTATION_SCHEMA_UNRECOGNIZED")
    if not packet_digest:
        issue_codes.append("CLOSURE_PACKET_DIGEST_MISSING")
    if _placeholder(closed_by):
        issue_codes.append("CLOSURE_HUMAN_CLOSER_ID_MISSING")
    if not closed_at_utc:
        issue_codes.append("CLOSURE_ATTESTED_AT_MISSING")
    if _placeholder(final_disposition):
        issue_codes.append("CLOSURE_FINAL_DISPOSITION_MISSING")
    if _placeholder(closure_statement):
        issue_codes.append("CLOSURE_STATEMENT_MISSING")
    escalated = []
    for key in (
        "closure_write_allowed",
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
        issue_codes.append("CLOSURE_AUTHORITY_ESCALATION_CLAIMED")
    verified = not issue_codes
    return {
        "closure_attestation_id": attestation_id,
        "schema_version": schema,
        "artifact_kind": _closure_value(raw, "artifact_kind") or "semantic_validator_handoff_closure_attestation",
        "artifact_path": str(path.as_posix()),
        "artifact_sha256": _sha256(path),
        "archive_gate_id": _closure_value(raw, "archive_gate_id", "source_archive_gate_id"),
        "archive_manifest_id": _closure_value(raw, "archive_manifest_id", "source_archive_manifest_id"),
        "custody_gate_id": _closure_value(raw, "custody_gate_id", "source_custody_gate_id"),
        "custody_seal_id": _closure_value(raw, "custody_seal_id", "source_custody_seal_id"),
        "signoff_gate_id": _closure_value(raw, "signoff_gate_id", "source_signoff_gate_id"),
        "decision_id": _closure_value(raw, "decision_id", "source_decision_id"),
        "chain_id": _closure_value(raw, "chain_id", "source_chain_id"),
        "experiment_id": _closure_value(raw, "experiment_id"),
        "archive_packet_digest": _closure_value(raw, "archive_packet_digest", "source_archive_packet_digest"),
        "closure_packet_digest": packet_digest,
        "final_disposition": final_disposition,
        "closure_statement": closure_statement,
        "closed_by": closed_by,
        "closed_at_utc": closed_at_utc,
        "trust_banner": _closure_value(raw, "trust_banner") or "TRUST_RESTRICTED",
        "verified": verified,
        "issue_codes": list(dict.fromkeys(issue_codes)),
        "authority_assertions": {
            "read_plane_only": bool(raw.get("read_plane_only", True)),
            "closure_write_allowed": _authority_assertion_true(raw, "closure_write_allowed"),
            "archive_write_allowed": _authority_assertion_true(raw, "archive_write_allowed"),
            "artifact_mutation_allowed": _authority_assertion_true(raw, "artifact_mutation_allowed"),
            "validator_submission_allowed": _authority_assertion_true(raw, "validator_submission_allowed"),
            "adjudication_allowed": _authority_assertion_true(raw, "adjudication_allowed"),
            "promotion_allowed": _authority_assertion_true(raw, "promotion_allowed"),
            "execution_allowed": _authority_assertion_true(raw, "execution_allowed"),
        },
        "raw_closure_attestation": raw,
    }


__all__ = [
    "_is_closure_attestation_candidate",
    "_closure_attestation_artifacts",
    "_normalize_closure_attestation",
]
