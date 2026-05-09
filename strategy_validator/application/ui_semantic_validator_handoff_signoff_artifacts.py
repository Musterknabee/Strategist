"""External operator signoff artifact discovery for semantic validator handoff."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_signoff_common import (
    _SIGNOFF_SCHEMA_VERSION,
    _authority_assertion_true,
    _norm,
    _placeholder,
    _read_json,
    _s,
    _sha256,
    _signoff_value,
)


def _is_signoff_candidate(raw: dict[str, Any]) -> bool:
    schema = _s(raw.get("schema_version"))
    if schema == _SIGNOFF_SCHEMA_VERSION:
        return True
    artifact_kind = _norm(raw.get("artifact_kind"))
    if artifact_kind in {"SEMANTIC_VALIDATOR_HANDOFF_OPERATOR_SIGNOFF", "OPERATOR_SIGNOFF", "VALIDATOR_HANDOFF_SIGNOFF"}:
        return True
    return bool(raw.get("decision_packet_digest") or raw.get("source_decision_packet_digest")) and bool(
        raw.get("human_signoff_statement") or raw.get("signoff_statement")
    )


def _normalize_signoff(path: Path, raw: dict[str, Any]) -> dict[str, Any]:
    issue_codes: list[str] = []
    schema = _s(raw.get("schema_version"))
    signoff_id = _signoff_value(raw, "signoff_id", "operator_signoff_id", "artifact_id") or path.stem
    decision_id = _signoff_value(raw, "decision_id", "source_decision_id")
    packet_digest = _signoff_value(raw, "decision_packet_digest", "source_decision_packet_digest", "packet_digest")
    reviewer_id = _signoff_value(raw, "human_reviewer_id", "reviewer_id", "operator_id")
    statement = _signoff_value(raw, "human_signoff_statement", "signoff_statement", "attestation_statement")
    signed_at_utc = _signoff_value(raw, "signed_at_utc", "signed_at", "created_at_utc")
    trust_banner = _signoff_value(raw, "trust_banner") or "TRUST_RESTRICTED"
    if schema != _SIGNOFF_SCHEMA_VERSION:
        issue_codes.append("SIGNOFF_SCHEMA_UNRECOGNIZED")
    if not decision_id:
        issue_codes.append("SIGNOFF_DECISION_ID_MISSING")
    if not packet_digest:
        issue_codes.append("SIGNOFF_DECISION_PACKET_DIGEST_MISSING")
    if _placeholder(reviewer_id):
        issue_codes.append("SIGNOFF_HUMAN_REVIEWER_ID_MISSING")
    if _placeholder(statement):
        issue_codes.append("SIGNOFF_HUMAN_STATEMENT_MISSING")
    if not signed_at_utc:
        issue_codes.append("SIGNOFF_SIGNED_AT_MISSING")
    escalated = []
    for key in ("validator_submission_allowed", "promotion_allowed", "execution_allowed", "artifact_mutation_allowed"):
        if _authority_assertion_true(raw, key):
            escalated.append(key)
    if escalated:
        issue_codes.append("SIGNOFF_AUTHORITY_ESCALATION_CLAIMED")
    verified = not issue_codes
    return {
        "signoff_id": signoff_id,
        "schema_version": schema,
        "artifact_kind": _signoff_value(raw, "artifact_kind") or "semantic_validator_handoff_operator_signoff",
        "artifact_path": str(path.as_posix()),
        "artifact_sha256": _sha256(path),
        "decision_id": decision_id,
        "review_id": _signoff_value(raw, "review_id", "source_review_id"),
        "chain_id": _signoff_value(raw, "chain_id", "source_chain_id"),
        "experiment_id": _signoff_value(raw, "experiment_id"),
        "decision_packet_digest": packet_digest,
        "human_reviewer_id": reviewer_id,
        "human_signoff_statement": statement,
        "signed_at_utc": signed_at_utc,
        "trust_banner": trust_banner,
        "verified": verified,
        "issue_codes": list(dict.fromkeys(issue_codes)),
        "authority_assertions": {
            "read_plane_only": bool(raw.get("read_plane_only", True)),
            "validator_submission_allowed": _authority_assertion_true(raw, "validator_submission_allowed"),
            "promotion_allowed": _authority_assertion_true(raw, "promotion_allowed"),
            "execution_allowed": _authority_assertion_true(raw, "execution_allowed"),
            "artifact_mutation_allowed": _authority_assertion_true(raw, "artifact_mutation_allowed"),
        },
        "raw_signoff": raw,
    }


def _signoff_artifacts(search_root: str | Path | None) -> list[dict[str, Any]]:
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
        if raw is None or not _is_signoff_candidate(raw):
            continue
        rows.append(_normalize_signoff(path, raw))
    return rows
