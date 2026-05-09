"""Custody row classification, matching, and filters."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_custody_common import (
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_SIGNOFF_STATUS,
    _RECORDED_STATUS,
    _as_list,
    _contains,
    _digest,
    _norm,
    _s,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_packet import (
    _custody_packet,
    _custody_template,
)


def _match_seals(signoff: dict[str, Any], seals: list[dict[str, Any]], custody_packet: dict[str, Any]) -> list[dict[str, Any]]:
    packet_digest = _s(custody_packet.get("packet_digest"))
    keys = {
        "signoff_gate_id": _s(signoff.get("signoff_gate_id")),
        "signoff_id": _s(signoff.get("signoff_id")),
        "decision_id": _s(signoff.get("decision_id")),
        "chain_id": _s(signoff.get("chain_id")),
        "experiment_id": _s(signoff.get("experiment_id")),
    }
    matched: list[dict[str, Any]] = []
    for seal in seals:
        if packet_digest and _s(seal.get("custody_packet_digest")) == packet_digest:
            matched.append(seal)
            continue
        for key, value in keys.items():
            if value and _s(seal.get(key)) == value:
                matched.append(seal)
                break
    return matched


def _custody_status(signoff: dict[str, Any], seal: dict[str, Any] | None, custody_packet: dict[str, Any]) -> str:
    if _s(signoff.get("signoff_status")) != _RECORDED_SIGNOFF_STATUS or not bool(signoff.get("signoff_recorded")):
        return _BLOCKED_STATUS
    if seal is None:
        return _READY_STATUS
    if _s(seal.get("custody_packet_digest")) != _s(custody_packet.get("packet_digest")):
        return _DIGEST_MISMATCH_STATUS
    if not bool(seal.get("verified")):
        return _INVALID_STATUS
    return _RECORDED_STATUS


def _issue_codes(signoff: dict[str, Any], seal: dict[str, Any] | None, status: str) -> list[str]:
    issues: list[str] = []
    issues.extend(_as_list(signoff.get("issue_codes")))
    if status == _BLOCKED_STATUS:
        issues.append("SIGNOFF_NOT_RECORDED_FOR_CUSTODY")
    if status == _READY_STATUS:
        issues.append("EXTERNAL_CUSTODY_SEAL_MISSING")
    if status == _DIGEST_MISMATCH_STATUS:
        issues.append("CUSTODY_PACKET_DIGEST_MISMATCH")
    if seal is not None:
        issues.extend(_as_list(seal.get("issue_codes")))
    return list(dict.fromkeys(issue for issue in issues if issue))


def _custody_row(signoff: dict[str, Any], seals: list[dict[str, Any]]) -> dict[str, Any]:
    custody_packet = _custody_packet(signoff)
    matched = _match_seals(signoff, seals, custody_packet)
    selected = matched[0] if matched else None
    status = _custody_status(signoff, selected, custody_packet)
    issues = _issue_codes(signoff, selected, status)
    recorded = status == _RECORDED_STATUS
    return {
        "custody_gate_id": "semantic-validator-custody-gate-" + _digest([signoff.get("signoff_gate_id"), custody_packet.get("packet_digest"), status])[:20],
        "custody_status": status,
        "custody_seal_recorded": recorded,
        "custody_seal_valid": recorded,
        "custody_seal_required": _s(signoff.get("signoff_status")) == _RECORDED_SIGNOFF_STATUS,
        "custody_seal_count": len(matched),
        "custody_seal_id": None if selected is None else selected.get("custody_seal_id"),
        "trust_banner": "TRUSTED" if recorded else signoff.get("trust_banner"),
        "signoff_gate_id": signoff.get("signoff_gate_id"),
        "signoff_id": signoff.get("signoff_id"),
        "signoff_status": signoff.get("signoff_status"),
        "decision_id": signoff.get("decision_id"),
        "review_id": signoff.get("review_id"),
        "chain_id": signoff.get("chain_id"),
        "chain_digest": signoff.get("chain_digest"),
        "experiment_id": signoff.get("experiment_id"),
        "decision_packet_digest": signoff.get("decision_packet_digest"),
        "custody_packet_digest": custody_packet.get("packet_digest"),
        "matched_custody_packet_digest": None if selected is None else selected.get("custody_packet_digest"),
        "human_reviewer_id": signoff.get("human_reviewer_id"),
        "human_custodian_id": None if selected is None else selected.get("human_custodian_id"),
        "sealed_at_utc": None if selected is None else selected.get("sealed_at_utc"),
        "issue_codes": issues,
        "issue_count": len(issues),
        "custody_packet": custody_packet,
        "custody_template": _custody_template(signoff, custody_packet),
        "matched_custody_seals": matched,
        "selected_custody_seal": selected,
        "source_signoff": signoff,
        "custody_seal_write_allowed": False,
        "archive_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "recommended_action": "HANDOFF_CUSTODY_SEAL_RECORDED_PREPARE_ARCHIVE_MANIFEST"
        if recorded
        else ("CREATE_EXTERNAL_CUSTODY_SEAL" if status == _READY_STATUS else "RETURN_TO_SIGNOFF_BEFORE_CUSTODY"),
        "summary_line": f"{signoff.get('experiment_id')} · {status} · custody_seals={len(matched)} · archive_write=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("custody_status")),
        _s(row.get("trust_banner")),
        _s(row.get("signoff_status")),
        _s(row.get("recommended_action")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    for seal in row.get("matched_custody_seals") or []:
        if isinstance(seal, dict):
            parts.extend(_as_list(seal.get("issue_codes")))
            parts.append(_s(seal.get("human_custodian_id")))
            parts.append(_s(seal.get("custody_seal_id")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    custody_status: set[str],
    trust_banner: set[str],
    custody_seal_recorded: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if custody_status and _norm(row.get("custody_status")) not in custody_status:
        return False
    if trust_banner and _norm(row.get("trust_banner")) not in trust_banner:
        return False
    if custody_seal_recorded is not None and bool(row.get("custody_seal_recorded")) is not custody_seal_recorded:
        return False
    return True
