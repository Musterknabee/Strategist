"""Row synthesis and filtering for semantic validator handoff signoff read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_signoff_common import (
    _AWAITING_STATUS,
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_DECISION_STATUS,
    _RECORDED_STATUS,
    _SIGNOFF_SCHEMA_VERSION,
    _as_list,
    _contains,
    _digest,
    _norm,
    _packet_digest,
    _s,
)


def _match_signoffs(decision: dict[str, Any], signoffs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    decision_id = _s(decision.get("decision_id"))
    packet_digest = _packet_digest(decision)
    review_id = _s(decision.get("review_id"))
    chain_id = _s(decision.get("chain_id"))
    experiment_id = _s(decision.get("experiment_id"))
    matched: list[dict[str, Any]] = []
    for signoff in signoffs:
        if decision_id and _s(signoff.get("decision_id")) == decision_id:
            matched.append(signoff)
            continue
        if packet_digest and _s(signoff.get("decision_packet_digest")) == packet_digest:
            matched.append(signoff)
            continue
        if review_id and _s(signoff.get("review_id")) == review_id:
            matched.append(signoff)
            continue
        if chain_id and _s(signoff.get("chain_id")) == chain_id:
            matched.append(signoff)
            continue
        if experiment_id and _s(signoff.get("experiment_id")) == experiment_id:
            matched.append(signoff)
    return matched


def _signoff_status(decision: dict[str, Any], signoff: dict[str, Any] | None) -> str:
    if not bool(decision.get("decision_ready")) or _s(decision.get("decision_status")) != _READY_DECISION_STATUS:
        return _BLOCKED_STATUS
    if signoff is None:
        return _AWAITING_STATUS
    if _s(signoff.get("decision_packet_digest")) != _packet_digest(decision):
        return _DIGEST_MISMATCH_STATUS
    if not bool(signoff.get("verified")):
        return _INVALID_STATUS
    if _s(signoff.get("decision_id")) and _s(signoff.get("decision_id")) != _s(decision.get("decision_id")):
        return _INVALID_STATUS
    return _RECORDED_STATUS


def _signoff_template(decision: dict[str, Any]) -> dict[str, Any]:
    packet = decision.get("decision_packet") if isinstance(decision.get("decision_packet"), dict) else {}
    return {
        "schema_version": _SIGNOFF_SCHEMA_VERSION,
        "signoff_id": f"semantic-validator-signoff-{_digest([decision.get('decision_id'), _packet_digest(decision)])[:20]}",
        "decision_id": decision.get("decision_id"),
        "review_id": decision.get("review_id"),
        "chain_id": decision.get("chain_id"),
        "experiment_id": decision.get("experiment_id"),
        "decision_packet_digest": _packet_digest(decision),
        "source_decision_status": decision.get("decision_status"),
        "source_trust_banner": decision.get("trust_banner"),
        "human_reviewer_id": "<REQUIRED_EXTERNALLY>",
        "human_signoff_statement": "<REQUIRED_EXTERNALLY>",
        "signed_at_utc": "<REQUIRED_EXTERNALLY>",
        "source_evidence": packet.get("source_evidence", {}),
        "authority_assertions": {
            "read_plane_only": True,
            "validator_submission_allowed": False,
            "promotion_allowed": False,
            "execution_allowed": False,
            "artifact_mutation_allowed": False,
        },
    }


def _issue_codes(decision: dict[str, Any], signoff: dict[str, Any] | None, status: str) -> list[str]:
    issues: list[str] = []
    issues.extend(_as_list(decision.get("decision_blocker_codes")))
    if status == _BLOCKED_STATUS:
        issues.append("DECISION_NOT_READY_FOR_OPERATOR_SIGNOFF")
    if status == _AWAITING_STATUS:
        issues.append("OPERATOR_SIGNOFF_MISSING")
    if status == _DIGEST_MISMATCH_STATUS:
        issues.append("SIGNOFF_DECISION_PACKET_DIGEST_MISMATCH")
    if signoff is not None:
        issues.extend(_as_list(signoff.get("issue_codes")))
        if _s(signoff.get("decision_id")) and _s(signoff.get("decision_id")) != _s(decision.get("decision_id")):
            issues.append("SIGNOFF_DECISION_ID_MISMATCH")
    return list(dict.fromkeys(issue for issue in issues if issue))


def _signoff_row(decision: dict[str, Any], signoffs: list[dict[str, Any]]) -> dict[str, Any]:
    matched = _match_signoffs(decision, signoffs)
    selected = matched[0] if matched else None
    status = _signoff_status(decision, selected)
    issues = _issue_codes(decision, selected, status)
    recorded = status == _RECORDED_STATUS
    receipt_digest = _digest(
        [
            decision.get("decision_id"),
            _packet_digest(decision),
            None if selected is None else selected.get("artifact_sha256"),
            status,
            "submit=false",
        ]
    )
    return {
        "signoff_gate_id": "semantic-validator-signoff-gate-" + receipt_digest[:20],
        "signoff_status": status,
        "signoff_recorded": recorded,
        "signoff_valid": recorded,
        "signoff_required": bool(decision.get("decision_ready")),
        "signoff_receipt_count": len(matched),
        "signoff_id": None if selected is None else selected.get("signoff_id"),
        "trust_banner": decision.get("trust_banner") if status != _RECORDED_STATUS else "TRUSTED",
        "decision_id": decision.get("decision_id"),
        "decision_status": decision.get("decision_status"),
        "decision_ready": decision.get("decision_ready"),
        "review_id": decision.get("review_id"),
        "chain_id": decision.get("chain_id"),
        "chain_digest": decision.get("chain_digest"),
        "experiment_id": decision.get("experiment_id"),
        "decision_packet_digest": _packet_digest(decision),
        "matched_signoff_packet_digest": None if selected is None else selected.get("decision_packet_digest"),
        "human_reviewer_id": None if selected is None else selected.get("human_reviewer_id"),
        "signed_at_utc": None if selected is None else selected.get("signed_at_utc"),
        "issue_codes": issues,
        "issue_count": len(issues),
        "signoff_template": _signoff_template(decision),
        "matched_signoffs": matched,
        "selected_signoff": selected,
        "source_decision": decision,
        "validator_submission_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "artifact_mutation_allowed": False,
        "recommended_action": "HANDOFF_SIGNOFF_RECEIPT_RECORDED_REVIEW_EXTERNAL_SUBMISSION_PATH"
        if recorded
        else ("WAIT_FOR_EXTERNAL_OPERATOR_SIGNOFF" if status == _AWAITING_STATUS else "RETURN_TO_DECISION_OR_REMEDIATION_BEFORE_SIGNOFF"),
        "summary_line": f"{decision.get('experiment_id')} · {status} · signoffs={len(matched)} · submit=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("signoff_status")),
        _s(row.get("trust_banner")),
        _s(row.get("decision_status")),
        _s(row.get("recommended_action")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    for signoff in row.get("matched_signoffs") or []:
        if isinstance(signoff, dict):
            parts.extend(_as_list(signoff.get("issue_codes")))
            parts.append(_s(signoff.get("human_reviewer_id")))
            parts.append(_s(signoff.get("signoff_id")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    signoff_status: set[str],
    trust_banner: set[str],
    signoff_recorded: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if signoff_status and _norm(row.get("signoff_status")) not in signoff_status:
        return False
    if trust_banner and _norm(row.get("trust_banner")) not in trust_banner:
        return False
    if signoff_recorded is not None and bool(row.get("signoff_recorded")) is not signoff_recorded:
        return False
    return True
