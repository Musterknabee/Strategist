"""Row synthesis and filtering for semantic validator handoff audit packets."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_common import (
    _DETAIL_ROUTES,
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _contains,
    _digest,
    _s,
)


def _packet_status(continuity: dict[str, Any], gaps: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> str:
    terminal_status = _s(continuity.get("terminal_status"))
    if any(bool(row.get("blocking")) or _s(row.get("gap_state")) == "BLOCKED" for row in gaps):
        return "BLOCKED_EVIDENCE_GAPS"
    if any(bool(row.get("blocked")) or _s(row.get("exception_state")) == "BLOCKED" for row in exceptions):
        return "OPEN_EXCEPTIONS_BLOCKING"
    if any(bool(row.get("external_artifact_required")) for row in gaps + exceptions):
        return "AWAITING_EXTERNAL_ARTIFACT"
    if terminal_status == "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION":
        return "CLOSED_AUDIT_READY"
    if bool(continuity.get("open_action")):
        return "OPEN_CHAIN_ACTION_REQUIRED"
    return "AUDIT_PACKET_REVIEW_REQUIRED"


def _packet_lane(status: str) -> str:
    if status == "CLOSED_AUDIT_READY":
        return "closed"
    if status == "AWAITING_EXTERNAL_ARTIFACT":
        return "external_artifact"
    if status.startswith("BLOCKED") or status.endswith("BLOCKING"):
        return "blocked"
    return "open"


def _trust_banner(status: str, continuity: dict[str, Any], gaps: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> str:
    source = _s(continuity.get("trust_banner"))
    if status == "CLOSED_AUDIT_READY" and source == "TRUSTED":
        return "TRUSTED"
    if status.startswith("BLOCKED") or any(_s(row.get("severity")) in {"CRITICAL", "HIGH", "BLOCKED"} for row in gaps + exceptions):
        return "UNTRUSTED"
    return "TRUST_RESTRICTED"


def _required_actions(status: str, continuity: dict[str, Any], gaps: list[dict[str, Any]], exceptions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    for row in gaps:
        actions.append(
            {
                "source": "evidence_gap",
                "source_id": row.get("gap_id"),
                "priority": row.get("priority") or "P2",
                "severity": row.get("severity") or "WARN",
                "operator_action": row.get("operator_action") or "INSPECT_EVIDENCE_GAP",
                "route": row.get("repair_route") or _DETAIL_ROUTES["evidence_gaps"],
                "issue_codes": _as_list(row.get("issue_codes")),
            }
        )
    for row in exceptions:
        actions.append(
            {
                "source": "exception",
                "source_id": row.get("exception_id"),
                "priority": row.get("priority") or "P2",
                "severity": row.get("severity") or "WARN",
                "operator_action": row.get("operator_action") or "INSPECT_HANDOFF_EXCEPTION",
                "route": row.get("next_route") or row.get("runbook_route") or _DETAIL_ROUTES["exceptions"],
                "issue_codes": _as_list(row.get("issue_codes")),
            }
        )
    if not actions and status != "CLOSED_AUDIT_READY":
        actions.append(
            {
                "source": "continuity",
                "source_id": continuity.get("continuity_id"),
                "priority": "P2",
                "severity": continuity.get("severity") or "WARN",
                "operator_action": continuity.get("recommended_action") or "INSPECT_HANDOFF_CONTINUITY",
                "route": continuity.get("continuity_route") or _DETAIL_ROUTES["continuity"],
                "issue_codes": _as_list(continuity.get("issue_codes")),
            }
        )
    return sorted(actions, key=lambda row: (_s(row.get("priority")), _s(row.get("severity")), _s(row.get("source_id"))))


def _timeline_tail(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(events, key=lambda row: int(row.get("stage_position") or 0))[-5:]


def _audit_packet_row(
    continuity: dict[str, Any],
    *,
    gaps: list[dict[str, Any]],
    exceptions: list[dict[str, Any]],
    timeline_events: list[dict[str, Any]],
) -> dict[str, Any]:
    status = _packet_status(continuity, gaps, exceptions)
    trust = _trust_banner(status, continuity, gaps, exceptions)
    actions = _required_actions(status, continuity, gaps, exceptions)
    issue_codes = sorted(
        dict.fromkeys(
            _as_list(continuity.get("issue_codes"))
            + [code for row in gaps for code in _as_list(row.get("issue_codes"))]
            + [code for row in exceptions for code in _as_list(row.get("issue_codes"))]
        )
    )
    digest_inputs = {
        "continuity_id": continuity.get("continuity_id"),
        "chain_id": continuity.get("chain_id"),
        "chain_digest": continuity.get("chain_digest"),
        "terminal_status": continuity.get("terminal_status"),
        "closure_status": continuity.get("closure_status"),
        "stage_path": [
            {
                "stage": stage.get("stage"),
                "record_id": stage.get("record_id"),
                "digest": stage.get("digest"),
                "ready": stage.get("ready"),
            }
            for stage in continuity.get("stage_path") or []
            if isinstance(stage, dict)
        ],
        "gap_ids": [row.get("gap_id") for row in gaps],
        "exception_ids": [row.get("exception_id") for row in exceptions],
        "issue_codes": issue_codes,
    }
    audit_digest = _digest(digest_inputs)
    packet_id = "semantic-validator-handoff-audit-packet-" + audit_digest[:20]
    external_count = sum(1 for row in gaps + exceptions if bool(row.get("external_artifact_required")))
    blocked_gap_count = sum(1 for row in gaps if bool(row.get("blocking")) or _s(row.get("gap_state")) == "BLOCKED")
    blocking_exception_count = sum(1 for row in exceptions if bool(row.get("blocked")) or _s(row.get("exception_state")) == "BLOCKED")
    packet_ready = status == "CLOSED_AUDIT_READY"
    return {
        "audit_packet_id": packet_id,
        "audit_packet_digest": audit_digest,
        "schema_version": _SCHEMA_VERSION,
        "experiment_id": continuity.get("experiment_id"),
        "continuity_id": continuity.get("continuity_id"),
        "chain_id": continuity.get("chain_id"),
        "chain_digest": continuity.get("chain_digest"),
        "terminal_status": continuity.get("terminal_status"),
        "current_stage": continuity.get("current_stage"),
        "closure_status": continuity.get("closure_status"),
        "packet_status": status,
        "packet_lane": _packet_lane(status),
        "trust_banner": trust,
        "audit_ready": packet_ready,
        "operator_attention_required": not packet_ready,
        "external_artifact_required": external_count > 0,
        "stage_count_expected": continuity.get("stage_count_expected"),
        "stage_count_present": continuity.get("stage_count_present"),
        "ready_stage_count": continuity.get("ready_stage_count"),
        "gap_count": len(gaps),
        "blocked_gap_count": blocked_gap_count,
        "exception_count": len(exceptions),
        "blocking_exception_count": blocking_exception_count,
        "external_artifact_gap_count": sum(1 for row in gaps if bool(row.get("external_artifact_required"))),
        "external_artifact_exception_count": sum(1 for row in exceptions if bool(row.get("external_artifact_required"))),
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "required_actions": actions,
        "required_action_count": len(actions),
        "stage_path": list(continuity.get("stage_path") or []),
        "timeline_tail": _timeline_tail(timeline_events),
        "evidence_gaps": gaps,
        "exceptions": exceptions,
        "routes": dict(_DETAIL_ROUTES),
        "authority": _authority(),
        "digest_inputs": digest_inputs,
        "source_continuity_row": continuity,
        "summary_line": f"{continuity.get('experiment_id')} · {status} · gaps={len(gaps)} exceptions={len(exceptions)} · execute=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get(k))
        for k in (
            "experiment_id",
            "audit_packet_id",
            "packet_status",
            "packet_lane",
            "trust_banner",
            "terminal_status",
            "current_stage",
            "closure_status",
            "summary_line",
        )
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    for action in row.get("required_actions") or []:
        if isinstance(action, dict):
            parts.extend([_s(action.get("operator_action")), _s(action.get("source_id"))])
            parts.extend(_as_list(action.get("issue_codes")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    packet_status: set[str],
    trust_banner: set[str],
    audit_ready: bool | None,
    operator_attention_required: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if packet_status and _s(row.get("packet_status")).upper() not in packet_status:
        return False
    if trust_banner and _s(row.get("trust_banner")).upper() not in trust_banner:
        return False
    if audit_ready is not None and bool(row.get("audit_ready")) is not audit_ready:
        return False
    if operator_attention_required is not None and bool(row.get("operator_attention_required")) is not operator_attention_required:
        return False
    return True
