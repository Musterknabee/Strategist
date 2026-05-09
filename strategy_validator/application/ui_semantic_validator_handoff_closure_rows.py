"""Closure gate row synthesis, status classification, and filtering."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_closure_common import (
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_STATUS,
    _VERIFIED_ARCHIVE_STATUS,
    _as_list,
    _contains,
    _digest,
    _norm,
    _s,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_packet import (
    _closure_packet,
    _closure_template,
)


def _match_attestations(
    archive: dict[str, Any], attestations: list[dict[str, Any]], closure_packet: dict[str, Any]
) -> list[dict[str, Any]]:
    packet_digest = _s(closure_packet.get("packet_digest"))
    keys = {
        "archive_gate_id": _s(archive.get("archive_gate_id")),
        "archive_manifest_id": _s(archive.get("archive_manifest_id")),
        "custody_gate_id": _s(archive.get("custody_gate_id")),
        "custody_seal_id": _s(archive.get("custody_seal_id")),
        "signoff_gate_id": _s(archive.get("signoff_gate_id")),
        "decision_id": _s(archive.get("decision_id")),
        "chain_id": _s(archive.get("chain_id")),
        "experiment_id": _s(archive.get("experiment_id")),
    }
    matched: list[dict[str, Any]] = []
    for attestation in attestations:
        if packet_digest and _s(attestation.get("closure_packet_digest")) == packet_digest:
            matched.append(attestation)
            continue
        for key, value in keys.items():
            if value and _s(attestation.get(key)) == value:
                matched.append(attestation)
                break
    return matched

def _closure_status(archive: dict[str, Any], attestation: dict[str, Any] | None, closure_packet: dict[str, Any]) -> str:
    if _s(archive.get("archive_status")) != _VERIFIED_ARCHIVE_STATUS or not bool(archive.get("archive_manifest_verified")):
        return _BLOCKED_STATUS
    if attestation is None:
        return _READY_STATUS
    if _s(attestation.get("closure_packet_digest")) != _s(closure_packet.get("packet_digest")):
        return _DIGEST_MISMATCH_STATUS
    if not bool(attestation.get("verified")):
        return _INVALID_STATUS
    return _RECORDED_STATUS

def _issue_codes(archive: dict[str, Any], attestation: dict[str, Any] | None, status: str) -> list[str]:
    issues: list[str] = []
    issues.extend(_as_list(archive.get("issue_codes")))
    if status == _BLOCKED_STATUS:
        issues.append("ARCHIVE_MANIFEST_NOT_VERIFIED_FOR_CLOSURE")
    if status == _READY_STATUS:
        issues.append("EXTERNAL_CLOSURE_ATTESTATION_MISSING")
    if status == _DIGEST_MISMATCH_STATUS:
        issues.append("CLOSURE_PACKET_DIGEST_MISMATCH")
    if attestation is not None:
        issues.extend(_as_list(attestation.get("issue_codes")))
    return list(dict.fromkeys(issue for issue in issues if issue))

def _closure_row(archive: dict[str, Any], attestations: list[dict[str, Any]]) -> dict[str, Any]:
    closure_packet = _closure_packet(archive)
    matched = _match_attestations(archive, attestations, closure_packet)
    selected = matched[0] if matched else None
    status = _closure_status(archive, selected, closure_packet)
    issues = _issue_codes(archive, selected, status)
    recorded = status == _RECORDED_STATUS
    return {
        "closure_gate_id": "semantic-validator-closure-gate-"
        + _digest([archive.get("archive_gate_id"), closure_packet.get("packet_digest"), status])[:20],
        "closure_status": status,
        "closure_attestation_recorded": recorded,
        "closure_attestation_required": _s(archive.get("archive_status")) == _VERIFIED_ARCHIVE_STATUS,
        "closure_attestation_count": len(matched),
        "closure_attestation_id": None if selected is None else selected.get("closure_attestation_id"),
        "trust_banner": "TRUSTED" if recorded else archive.get("trust_banner"),
        "archive_gate_id": archive.get("archive_gate_id"),
        "archive_manifest_id": archive.get("archive_manifest_id"),
        "archive_status": archive.get("archive_status"),
        "custody_gate_id": archive.get("custody_gate_id"),
        "custody_seal_id": archive.get("custody_seal_id"),
        "signoff_gate_id": archive.get("signoff_gate_id"),
        "signoff_id": archive.get("signoff_id"),
        "decision_id": archive.get("decision_id"),
        "review_id": archive.get("review_id"),
        "chain_id": archive.get("chain_id"),
        "chain_digest": archive.get("chain_digest"),
        "experiment_id": archive.get("experiment_id"),
        "decision_packet_digest": archive.get("decision_packet_digest"),
        "custody_packet_digest": archive.get("custody_packet_digest"),
        "archive_packet_digest": archive.get("archive_packet_digest"),
        "closure_packet_digest": closure_packet.get("packet_digest"),
        "matched_closure_packet_digest": None if selected is None else selected.get("closure_packet_digest"),
        "archive_root": archive.get("archive_root"),
        "manifest_artifact_count": archive.get("manifest_artifact_count"),
        "archived_by": archive.get("archived_by"),
        "archive_created_at_utc": archive.get("created_at_utc"),
        "final_disposition": None if selected is None else selected.get("final_disposition"),
        "closure_statement": None if selected is None else selected.get("closure_statement"),
        "closed_by": None if selected is None else selected.get("closed_by"),
        "closed_at_utc": None if selected is None else selected.get("closed_at_utc"),
        "issue_codes": issues,
        "issue_count": len(issues),
        "closure_packet": closure_packet,
        "closure_template": _closure_template(archive, closure_packet),
        "matched_closure_attestations": matched,
        "selected_closure_attestation": selected,
        "source_archive": archive,
        "closure_write_allowed": False,
        "archive_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "recommended_action": "HANDOFF_CLOSURE_RECORDED_RETAIN_AUDIT_TRAIL"
        if recorded
        else ("CREATE_EXTERNAL_CLOSURE_ATTESTATION" if status == _READY_STATUS else "RETURN_TO_ARCHIVE_VERIFICATION_BEFORE_CLOSURE"),
        "summary_line": f"{archive.get('experiment_id')} · {status} · attestations={len(matched)} · execute=false",
    }

def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("closure_status")),
        _s(row.get("trust_banner")),
        _s(row.get("archive_status")),
        _s(row.get("recommended_action")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    for attestation in row.get("matched_closure_attestations") or []:
        if isinstance(attestation, dict):
            parts.extend(_as_list(attestation.get("issue_codes")))
            parts.append(_s(attestation.get("closure_attestation_id")))
            parts.append(_s(attestation.get("closed_by")))
            parts.append(_s(attestation.get("final_disposition")))
    return "\n".join(parts)

def _matches(
    row: dict[str, Any], *, experiment_id_contains: str | None, issue_contains: str | None, closure_status: set[str], trust_banner: set[str], closure_attestation_recorded: bool | None
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if closure_status and _norm(row.get("closure_status")) not in closure_status:
        return False
    if trust_banner and _norm(row.get("trust_banner")) not in trust_banner:
        return False
    if closure_attestation_recorded is not None and bool(row.get("closure_attestation_recorded")) is not closure_attestation_recorded:
        return False
    return True


__all__ = [
    "_match_attestations",
    "_closure_status",
    "_issue_codes",
    "_closure_row",
    "_haystack",
    "_matches",
]
