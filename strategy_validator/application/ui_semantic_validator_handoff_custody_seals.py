"""External custody seal discovery and normalization."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_custody_common import (
    _CUSTODY_SEAL_SCHEMA_VERSION,
    _authority_assertion_true,
    _norm,
    _placeholder,
    _read_json,
    _s,
    _seal_value,
    _sha256,
)


def _is_custody_seal_candidate(raw: dict[str, Any]) -> bool:
    schema = _s(raw.get("schema_version"))
    if schema == _CUSTODY_SEAL_SCHEMA_VERSION:
        return True
    artifact_kind = _norm(raw.get("artifact_kind"))
    if artifact_kind in {"SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_SEAL", "CUSTODY_SEAL", "VALIDATOR_HANDOFF_CUSTODY_SEAL"}:
        return True
    return bool(raw.get("custody_packet_digest") or raw.get("source_custody_packet_digest")) and bool(
        raw.get("custodian_id") or raw.get("human_custodian_id") or raw.get("sealed_by")
    )


def _custody_seal_artifacts(search_root: str | Path | None) -> list[dict[str, Any]]:
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
        if raw is None or not _is_custody_seal_candidate(raw):
            continue
        rows.append(_normalize_custody_seal(path, raw))
    return rows


def _normalize_custody_seal(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    issue_codes: list[str] = []
    schema = _s(raw.get("schema_version"))
    seal_id = _seal_value(raw, "custody_seal_id", "seal_id", "artifact_id") or path.stem
    packet_digest = _seal_value(raw, "custody_packet_digest", "source_custody_packet_digest", "packet_digest")
    custodian_id = _seal_value(raw, "human_custodian_id", "custodian_id", "sealed_by", "operator_id")
    statement = _seal_value(raw, "custody_statement", "seal_statement", "attestation_statement")
    sealed_at_utc = _seal_value(raw, "sealed_at_utc", "sealed_at", "created_at_utc")
    if schema != _CUSTODY_SEAL_SCHEMA_VERSION:
        issue_codes.append("CUSTODY_SEAL_SCHEMA_UNRECOGNIZED")
    if not packet_digest:
        issue_codes.append("CUSTODY_PACKET_DIGEST_MISSING")
    if _placeholder(custodian_id):
        issue_codes.append("CUSTODY_CUSTODIAN_ID_MISSING")
    if _placeholder(statement):
        issue_codes.append("CUSTODY_STATEMENT_MISSING")
    if not sealed_at_utc:
        issue_codes.append("CUSTODY_SEALED_AT_MISSING")
    escalated = []
    for key in (
        "custody_seal_write_allowed",
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
        issue_codes.append("CUSTODY_AUTHORITY_ESCALATION_CLAIMED")
    verified = not issue_codes
    return {
        "custody_seal_id": seal_id,
        "schema_version": schema,
        "artifact_kind": _seal_value(raw, "artifact_kind") or "semantic_validator_handoff_custody_seal",
        "artifact_path": str(path.as_posix()),
        "artifact_sha256": _sha256(path),
        "signoff_gate_id": _seal_value(raw, "signoff_gate_id", "source_signoff_gate_id"),
        "signoff_id": _seal_value(raw, "signoff_id", "source_signoff_id"),
        "decision_id": _seal_value(raw, "decision_id", "source_decision_id"),
        "chain_id": _seal_value(raw, "chain_id", "source_chain_id"),
        "experiment_id": _seal_value(raw, "experiment_id"),
        "custody_packet_digest": packet_digest,
        "human_custodian_id": custodian_id,
        "custody_statement": statement,
        "sealed_at_utc": sealed_at_utc,
        "trust_banner": _seal_value(raw, "trust_banner") or "TRUST_RESTRICTED",
        "verified": verified,
        "issue_codes": list(dict.fromkeys(issue_codes)),
        "authority_assertions": {
            "read_plane_only": bool(raw.get("read_plane_only", True)),
            "custody_seal_write_allowed": _authority_assertion_true(raw, "custody_seal_write_allowed"),
            "archive_write_allowed": _authority_assertion_true(raw, "archive_write_allowed"),
            "artifact_mutation_allowed": _authority_assertion_true(raw, "artifact_mutation_allowed"),
            "validator_submission_allowed": _authority_assertion_true(raw, "validator_submission_allowed"),
            "adjudication_allowed": _authority_assertion_true(raw, "adjudication_allowed"),
            "promotion_allowed": _authority_assertion_true(raw, "promotion_allowed"),
            "execution_allowed": _authority_assertion_true(raw, "execution_allowed"),
        },
        "raw_custody_seal": raw,
    }
