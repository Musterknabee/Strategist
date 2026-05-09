"""Timeline event row synthesis for semantic validator handoff continuity chains."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_timeline_common import (
    _STAGE_ORDER,
    _as_list,
    _authority,
    _contains,
    _norm,
    _s,
)


def _event_state(continuity: dict[str, Any], stage: dict[str, Any]) -> str:
    stage_key = _s(stage.get("stage"))
    terminal_status = _s(continuity.get("terminal_status"))
    if not bool(stage.get("present")):
        return "MISSING_EVIDENCE"
    if bool(continuity.get("external_artifact_required")) and stage_key == "closure":
        return "AWAITING_EXTERNAL_ARTIFACT"
    if _as_list(stage.get("issue_codes")):
        return "BLOCKED" if terminal_status.startswith("BLOCKED") or _s(continuity.get("severity")) == "BLOCKED" else "ATTENTION_REQUIRED"
    if bool(continuity.get("open_action")) and stage_key == _s(continuity.get("current_stage")):
        return "CURRENT_OPEN_STAGE"
    return "RECORDED_READY"


def _event_severity(event_state: str) -> str:
    if event_state == "BLOCKED":
        return "BLOCKED"
    if event_state in {"MISSING_EVIDENCE", "AWAITING_EXTERNAL_ARTIFACT", "ATTENTION_REQUIRED", "CURRENT_OPEN_STAGE"}:
        return "WARN"
    return "INFO"


def _operator_focus(event_state: str, stage_key: str) -> str:
    if event_state == "MISSING_EVIDENCE":
        return f"RESTORE_{stage_key.upper()}_EVIDENCE"
    if event_state == "BLOCKED":
        return "REPAIR_BLOCKED_HANDOFF_STAGE"
    if event_state == "AWAITING_EXTERNAL_ARTIFACT":
        return "CREATE_EXTERNAL_CLOSURE_ATTESTATION"
    if event_state == "ATTENTION_REQUIRED":
        return "REVIEW_HANDOFF_STAGE_ISSUES"
    if event_state == "CURRENT_OPEN_STAGE":
        return "FOLLOW_CURRENT_HANDOFF_STAGE_RUNBOOK"
    return "RETAIN_STAGE_AUDIT_EVIDENCE"


def _timeline_event(continuity: dict[str, Any], stage: dict[str, Any], index: int) -> dict[str, Any]:
    stage_key = _s(stage.get("stage")) or f"stage-{index}"
    event_state = _event_state(continuity, stage)
    issue_codes = _as_list(stage.get("issue_codes"))
    external_required = bool(continuity.get("external_artifact_required")) and stage_key == "closure"
    experiment_id = _s(continuity.get("experiment_id")) or "UNKNOWN"
    return {
        "timeline_event_id": f"semantic-validator-handoff-timeline-{experiment_id}-{stage_key}-{index}",
        "continuity_id": continuity.get("continuity_id"),
        "experiment_id": continuity.get("experiment_id"),
        "chain_id": continuity.get("chain_id"),
        "chain_digest": continuity.get("chain_digest"),
        "terminal_status": continuity.get("terminal_status"),
        "current_stage": continuity.get("current_stage"),
        "closure_status": continuity.get("closure_status"),
        "trust_banner": continuity.get("trust_banner"),
        "stage": stage_key,
        "stage_label": stage.get("label") or stage_key,
        "stage_position": int(_STAGE_ORDER.get(stage_key, index + 1)),
        "stage_route": stage.get("route"),
        "stage_status": stage.get("status"),
        "record_id": stage.get("record_id"),
        "digest": stage.get("digest"),
        "present": bool(stage.get("present")),
        "ready": bool(stage.get("ready")),
        "event_state": event_state,
        "severity": _event_severity(event_state),
        "blocking": event_state in {"BLOCKED", "MISSING_EVIDENCE", "AWAITING_EXTERNAL_ARTIFACT", "ATTENTION_REQUIRED"},
        "external_artifact_required": external_required,
        "next_external_artifact_kind": continuity.get("next_external_artifact_kind") if external_required else None,
        "next_external_schema_version": continuity.get("next_external_schema_version") if external_required else None,
        "operator_focus": _operator_focus(event_state, stage_key),
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "source_route": "/ui/semantic-validator-handoff/continuity",
        "continuity_route": continuity.get("continuity_route") or "/ui/semantic-validator-handoff/continuity",
        "runbook_route": "/ui/semantic-validator-handoff/runbook",
        "exceptions_route": "/ui/semantic-validator-handoff/exceptions",
        "authority": _authority(),
        "summary_line": f"{experiment_id} · {stage_key} · {event_state} · execute=false",
    }


def _timeline_events(continuity: dict[str, Any]) -> list[dict[str, Any]]:
    stages = continuity.get("stage_path")
    if not isinstance(stages, list):
        return []
    return [_timeline_event(continuity, stage, i) for i, stage in enumerate(stages) if isinstance(stage, dict)]


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get(k))
        for k in (
            "experiment_id",
            "continuity_id",
            "terminal_status",
            "current_stage",
            "stage",
            "stage_status",
            "event_state",
            "operator_focus",
            "summary_line",
        )
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    stage: set[str],
    event_state: set[str],
    severity: set[str],
    include_ready: bool,
) -> bool:
    if not include_ready and row.get("event_state") == "RECORDED_READY":
        return False
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if stage and _norm(row.get("stage")) not in stage:
        return False
    if event_state and _norm(row.get("event_state")) not in event_state:
        return False
    if severity and _norm(row.get("severity")) not in severity:
        return False
    return True


__all__ = [
    "_event_state",
    "_event_severity",
    "_operator_focus",
    "_timeline_event",
    "_timeline_events",
    "_haystack",
    "_matches",
]
