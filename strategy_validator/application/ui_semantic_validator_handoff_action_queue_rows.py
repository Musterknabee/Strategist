"""Row construction and filtering for semantic validator handoff action queues."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_action_queue_common import (
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)


def _queue_state(packet: dict[str, Any], action: dict[str, Any]) -> str:
    if (
        bool(action.get("blocked"))
        or _norm(action.get("severity")) in {"CRITICAL", "HIGH", "BLOCKED"}
        or _s(packet.get("packet_lane")) == "blocked"
    ):
        return "BLOCKED_ACTION_REQUIRED"
    if (
        bool(action.get("external_artifact_required"))
        or _s(packet.get("packet_lane")) == "external_artifact"
        or _s(packet.get("packet_status")) == "AWAITING_EXTERNAL_ARTIFACT"
    ):
        return "EXTERNAL_ARTIFACT_REQUIRED"
    return "OPERATOR_ACTION_REQUIRED"


def _action_id(packet: dict[str, Any], action: dict[str, Any], index: int) -> str:
    return "semantic-validator-handoff-action-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "packet": packet.get("audit_packet_id"),
            "digest": packet.get("audit_packet_digest"),
            "source": action.get("source"),
            "source_id": action.get("source_id"),
            "idx": index,
        }
    )[:20]


def _row(packet: dict[str, Any], action: dict[str, Any], index: int) -> dict[str, Any]:
    state = _queue_state(packet, action)
    issue_codes = _as_list(action.get("issue_codes"))
    return {
        "action_id": _action_id(packet, action, index),
        "schema_version": _SCHEMA_VERSION,
        "audit_packet_id": packet.get("audit_packet_id"),
        "audit_packet_digest": packet.get("audit_packet_digest"),
        "experiment_id": packet.get("experiment_id"),
        "continuity_id": packet.get("continuity_id"),
        "chain_id": packet.get("chain_id"),
        "chain_digest": packet.get("chain_digest"),
        "packet_status": packet.get("packet_status"),
        "packet_lane": packet.get("packet_lane"),
        "trust_banner": packet.get("trust_banner") or "TRUST_RESTRICTED",
        "audit_ready": bool(packet.get("audit_ready")),
        "operator_attention_required": bool(packet.get("operator_attention_required")),
        "queue_state": state,
        "priority": action.get("priority") or "P2",
        "severity": action.get("severity") or "WARN",
        "source": action.get("source") or "audit_packet",
        "source_id": action.get("source_id"),
        "operator_action": action.get("operator_action") or "INSPECT_SEMANTIC_VALIDATOR_HANDOFF_ACTION",
        "route": action.get("route") or "/ui/semantic-validator-handoff/audit-packet",
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "external_artifact_required": state == "EXTERNAL_ARTIFACT_REQUIRED"
        or bool(action.get("external_artifact_required")),
        "blocked": state == "BLOCKED_ACTION_REQUIRED" or bool(action.get("blocked")),
        "safe_next_step": "OPEN_READ_PLANE_ROUTE_AND_REVIEW",
        "action_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "authority": _authority(),
        "source_action": action,
        "source_packet_summary": {
            "packet_status": packet.get("packet_status"),
            "packet_lane": packet.get("packet_lane"),
            "trust_banner": packet.get("trust_banner"),
        },
        "summary_line": f"{packet.get('experiment_id')} · {state} · {action.get('priority') or 'P2'}/{action.get('severity') or 'WARN'} · {action.get('operator_action')} · execute=false",
    }


def _sort_key(row: dict[str, Any]) -> tuple[int, int, str, str]:
    return (
        {"P0": 0, "P1": 1, "P2": 2, "P3": 3}.get(_norm(row.get("priority")), 9),
        {"CRITICAL": 0, "HIGH": 1, "BLOCKED": 1, "WARN": 2, "MEDIUM": 2, "LOW": 3}.get(
            _norm(row.get("severity")), 9
        ),
        _s(row.get("experiment_id")),
        _s(row.get("action_id")),
    )


def _hay(row: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(row.get(key))
            for key in (
                "experiment_id",
                "action_id",
                "audit_packet_id",
                "queue_state",
                "priority",
                "severity",
                "trust_banner",
                "source",
                "source_id",
                "operator_action",
                "route",
                "summary_line",
            )
        ]
        + _as_list(row.get("issue_codes"))
    )


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    queue_state: set[str] | None = None,
    priority: set[str] | None = None,
    severity: set[str] | None = None,
    trust_banner: set[str] | None = None,
    source: set[str] | None = None,
    external_artifact_required: bool | None = None,
    blocked: bool | None = None,
) -> bool:
    queue_state = queue_state or set()
    priority = priority or set()
    severity = severity or set()
    trust_banner = trust_banner or set()
    source = source or set()
    return (
        _contains(row.get("experiment_id"), experiment_id_contains)
        and (not issue_contains or _contains(_hay(row), issue_contains))
        and (not queue_state or _norm(row.get("queue_state")) in queue_state)
        and (not priority or _norm(row.get("priority")) in priority)
        and (not severity or _norm(row.get("severity")) in severity)
        and (not trust_banner or _norm(row.get("trust_banner")) in trust_banner)
        and (not source or _norm(row.get("source")) in source)
        and (
            external_artifact_required is None
            or bool(row.get("external_artifact_required")) is external_artifact_required
        )
        and (blocked is None or bool(row.get("blocked")) is blocked)
    )
