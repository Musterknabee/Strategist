"""Archive row matching, status classification, and filters."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_archive_common import (
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_CUSTODY_STATUS,
    _VERIFIED_STATUS,
    _as_list,
    _contains,
    _digest,
    _norm,
    _s,
)
from strategy_validator.application.ui_semantic_validator_handoff_archive_packet import (
    _archive_packet,
    _archive_template,
)


def _match_manifests(custody: dict[str, Any], manifests: list[dict[str, Any]], archive_packet: dict[str, Any]) -> list[dict[str, Any]]:
    packet_digest = _s(archive_packet.get("packet_digest"))
    keys = {
        "custody_gate_id": _s(custody.get("custody_gate_id")),
        "custody_seal_id": _s(custody.get("custody_seal_id")),
        "signoff_gate_id": _s(custody.get("signoff_gate_id")),
        "decision_id": _s(custody.get("decision_id")),
        "chain_id": _s(custody.get("chain_id")),
        "experiment_id": _s(custody.get("experiment_id")),
    }
    matched: list[dict[str, Any]] = []
    for manifest in manifests:
        if packet_digest and _s(manifest.get("archive_packet_digest")) == packet_digest:
            matched.append(manifest)
            continue
        for key, value in keys.items():
            if value and _s(manifest.get(key)) == value:
                matched.append(manifest)
                break
    return matched


def _archive_status(custody: dict[str, Any], manifest: dict[str, Any] | None, archive_packet: dict[str, Any]) -> str:
    if _s(custody.get("custody_status")) != _RECORDED_CUSTODY_STATUS or not bool(custody.get("custody_seal_recorded")):
        return _BLOCKED_STATUS
    if manifest is None:
        return _READY_STATUS
    if _s(manifest.get("archive_packet_digest")) != _s(archive_packet.get("packet_digest")):
        return _DIGEST_MISMATCH_STATUS
    if not bool(manifest.get("verified")):
        return _INVALID_STATUS
    return _VERIFIED_STATUS


def _issue_codes(custody: dict[str, Any], manifest: dict[str, Any] | None, status: str) -> list[str]:
    issues: list[str] = []
    issues.extend(_as_list(custody.get("issue_codes")))
    if status == _BLOCKED_STATUS:
        issues.append("CUSTODY_SEAL_NOT_RECORDED_FOR_ARCHIVE")
    if status == _READY_STATUS:
        issues.append("EXTERNAL_ARCHIVE_MANIFEST_MISSING")
    if status == _DIGEST_MISMATCH_STATUS:
        issues.append("ARCHIVE_PACKET_DIGEST_MISMATCH")
    if manifest is not None:
        issues.extend(_as_list(manifest.get("issue_codes")))
    return list(dict.fromkeys(issue for issue in issues if issue))


def _archive_row(custody: dict[str, Any], manifests: list[dict[str, Any]]) -> dict[str, Any]:
    archive_packet = _archive_packet(custody)
    matched = _match_manifests(custody, manifests, archive_packet)
    selected = matched[0] if matched else None
    status = _archive_status(custody, selected, archive_packet)
    issues = _issue_codes(custody, selected, status)
    verified = status == _VERIFIED_STATUS
    return {
        "archive_gate_id": "semantic-validator-archive-gate-" + _digest([custody.get("custody_gate_id"), archive_packet.get("packet_digest"), status])[:20],
        "archive_status": status,
        "archive_manifest_verified": verified,
        "archive_manifest_required": _s(custody.get("custody_status")) == _RECORDED_CUSTODY_STATUS,
        "archive_manifest_count": len(matched),
        "archive_manifest_id": None if selected is None else selected.get("archive_manifest_id"),
        "trust_banner": "TRUSTED" if verified else custody.get("trust_banner"),
        "custody_gate_id": custody.get("custody_gate_id"),
        "custody_seal_id": custody.get("custody_seal_id"),
        "custody_status": custody.get("custody_status"),
        "signoff_gate_id": custody.get("signoff_gate_id"),
        "signoff_id": custody.get("signoff_id"),
        "decision_id": custody.get("decision_id"),
        "review_id": custody.get("review_id"),
        "chain_id": custody.get("chain_id"),
        "chain_digest": custody.get("chain_digest"),
        "experiment_id": custody.get("experiment_id"),
        "decision_packet_digest": custody.get("decision_packet_digest"),
        "custody_packet_digest": custody.get("custody_packet_digest"),
        "archive_packet_digest": archive_packet.get("packet_digest"),
        "matched_archive_packet_digest": None if selected is None else selected.get("archive_packet_digest"),
        "archive_root": None if selected is None else selected.get("archive_root"),
        "manifest_artifact_count": None if selected is None else selected.get("manifest_artifact_count"),
        "archived_by": None if selected is None else selected.get("archived_by"),
        "created_at_utc": None if selected is None else selected.get("created_at_utc"),
        "issue_codes": issues,
        "issue_count": len(issues),
        "archive_packet": archive_packet,
        "archive_template": _archive_template(custody, archive_packet),
        "matched_archive_manifests": matched,
        "selected_archive_manifest": selected,
        "source_custody": custody,
        "archive_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "recommended_action": "HANDOFF_ARCHIVE_MANIFEST_VERIFIED_RETAIN_FOR_AUDIT" if verified else ("CREATE_EXTERNAL_ARCHIVE_MANIFEST" if status == _READY_STATUS else "RETURN_TO_CUSTODY_BEFORE_ARCHIVE"),
        "summary_line": f"{custody.get('experiment_id')} · {status} · manifests={len(matched)} · submit=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [_s(row.get("archive_status")), _s(row.get("trust_banner")), _s(row.get("custody_status")), _s(row.get("recommended_action")), _s(row.get("summary_line"))]
    parts.extend(_as_list(row.get("issue_codes")))
    for manifest in row.get("matched_archive_manifests") or []:
        if isinstance(manifest, dict):
            parts.extend(_as_list(manifest.get("issue_codes")))
            parts.append(_s(manifest.get("archive_manifest_id")))
            parts.append(_s(manifest.get("archived_by")))
            parts.append(_s(manifest.get("archive_root")))
    return "\n".join(parts)


def _matches(row: dict[str, Any], *, experiment_id_contains: str | None, issue_contains: str | None, archive_status: set[str], trust_banner: set[str], archive_manifest_verified: bool | None) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if archive_status and _norm(row.get("archive_status")) not in archive_status:
        return False
    if trust_banner and _norm(row.get("trust_banner")) not in trust_banner:
        return False
    if archive_manifest_verified is not None and bool(row.get("archive_manifest_verified")) is not archive_manifest_verified:
        return False
    return True
