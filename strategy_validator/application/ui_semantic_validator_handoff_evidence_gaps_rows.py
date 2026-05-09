"""Evidence-gap row synthesis for semantic validator handoff timeline events."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_common import (
    _as_list,
    _authority,
    _contains,
    _norm,
    _s,
)


def _classify(event: dict[str, Any]) -> tuple[str, str, str, str]:
    state = _s(event.get("event_state"))
    stage = _s(event.get("stage")) or "stage"
    if state == "MISSING_EVIDENCE":
        return "MISSING_STAGE_EVIDENCE_GAP", "BLOCKED", "P0", "RESTORE_STAGE_EVIDENCE_EXTERNALLY"
    if state == "BLOCKED":
        return "BLOCKED_STAGE_EVIDENCE_GAP", "BLOCKED", "P0", "REPAIR_BLOCKED_HANDOFF_STAGE_EXTERNALLY"
    if state == "AWAITING_EXTERNAL_ARTIFACT" or bool(event.get("external_artifact_required")):
        return "EXTERNAL_ARTIFACT_GAP", "AWAITING_EXTERNAL_ARTIFACT", "P1", "CREATE_EXTERNAL_ARTIFACT_EXTERNALLY"
    if state == "ATTENTION_REQUIRED":
        return "ATTENTION_STAGE_EVIDENCE_GAP", "ATTENTION_REQUIRED", "P2", "REVIEW_STAGE_EVIDENCE_ISSUES"
    if state == "CURRENT_OPEN_STAGE":
        return "CURRENT_STAGE_OPEN_GAP", "OPEN", "P2", f"COMPLETE_{stage.upper()}_STAGE_EXTERNALLY"
    return "RESOLVED_AUDIT_REFERENCE", "RESOLVED", "P4", "RETAIN_AUDIT_TRAIL"


def _repair_route(event: dict[str, Any], kind: str) -> str:
    if kind == "EXTERNAL_ARTIFACT_GAP":
        return "/ui/semantic-validator-handoff/closure"
    stage = _s(event.get("stage"))
    return f"/ui/semantic-validator-handoff/{stage}" if stage else "/ui/semantic-validator-handoff/continuity"


def _checklist(kind: str, event: dict[str, Any]) -> list[str]:
    stage = _s(event.get("stage")) or "stage"
    if kind == "MISSING_STAGE_EVIDENCE_GAP":
        return [
            f"Open the {stage} stage read-plane and identify the missing evidence record.",
            "Restore or regenerate the missing upstream evidence artifact outside this read-plane.",
            "Refresh timeline and continuity projections after the artifact exists.",
            "Confirm validator submission/adjudication/promotion/execution remain out of scope.",
        ]
    if kind == "BLOCKED_STAGE_EVIDENCE_GAP":
        return [
            "Inspect issue_codes and digest fields for the blocked stage.",
            "Repair the source evidence artifact externally without mutating this projection.",
            "Refresh the semantic validator handoff chain read-planes after repair.",
            "Keep the digest chain intact; do not bypass governance gates.",
        ]
    if kind == "EXTERNAL_ARTIFACT_GAP":
        artifact_kind = _s(event.get("next_external_artifact_kind")) or "required external artifact"
        schema = _s(event.get("next_external_schema_version")) or "declared schema"
        return [
            f"Create the required external artifact: {artifact_kind}.",
            f"Use schema/version: {schema}.",
            "Keep source packet and chain digests unchanged when preparing the artifact.",
            "Refresh closure, continuity, timeline, and evidence-gap read-planes after recording it externally.",
        ]
    if kind == "ATTENTION_STAGE_EVIDENCE_GAP":
        return [
            "Review stage issue codes and supporting digest fields.",
            "Resolve warning-level evidence ambiguity outside this read-plane.",
            "Refresh the stage route and continuity cockpit after resolution.",
        ]
    if kind == "CURRENT_STAGE_OPEN_GAP":
        return [
            f"Continue the currently open {stage} stage using the existing runbook.",
            "Do not treat an open stage as submission, adjudication, promotion, or execution authority.",
            "Refresh continuity after the external prerequisite is resolved.",
        ]
    return ["Retain recorded evidence as an audit reference.", "No repair is required for this resolved stage."]


def _gap_row(event: dict[str, Any], index: int) -> dict[str, Any]:
    kind, state, priority, action = _classify(event)
    stage = _s(event.get("stage")) or "stage"
    experiment_id = _s(event.get("experiment_id")) or "UNKNOWN"
    issue_codes = _as_list(event.get("issue_codes"))
    return {
        "gap_id": f"semantic-validator-handoff-gap-{experiment_id}-{stage}-{kind}-{index}",
        "timeline_event_id": event.get("timeline_event_id"),
        "continuity_id": event.get("continuity_id"),
        "experiment_id": event.get("experiment_id"),
        "chain_id": event.get("chain_id"),
        "chain_digest": event.get("chain_digest"),
        "terminal_status": event.get("terminal_status"),
        "current_stage": event.get("current_stage"),
        "closure_status": event.get("closure_status"),
        "stage": stage,
        "stage_label": event.get("stage_label") or stage,
        "stage_position": event.get("stage_position"),
        "stage_status": event.get("stage_status"),
        "stage_route": event.get("stage_route"),
        "record_id": event.get("record_id"),
        "digest": event.get("digest"),
        "present": bool(event.get("present")),
        "ready": bool(event.get("ready")),
        "event_state": event.get("event_state"),
        "gap_kind": kind,
        "gap_state": state,
        "priority": priority,
        "severity": _s(event.get("severity")) or ("INFO" if state == "RESOLVED" else "WARN"),
        "blocking": bool(event.get("blocking")) or state == "BLOCKED",
        "resolved": state == "RESOLVED",
        "external_artifact_required": bool(event.get("external_artifact_required")),
        "required_external_artifact_kind": event.get("next_external_artifact_kind"),
        "required_external_schema_version": event.get("next_external_schema_version"),
        "operator_action": action,
        "operator_checklist": _checklist(kind, event),
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "repair_route": _repair_route(event, kind),
        "source_route": "/ui/semantic-validator-handoff/timeline",
        "timeline_route": "/ui/semantic-validator-handoff/timeline",
        "continuity_route": event.get("continuity_route") or "/ui/semantic-validator-handoff/continuity",
        "runbook_route": event.get("runbook_route") or "/ui/semantic-validator-handoff/runbook",
        "exceptions_route": event.get("exceptions_route") or "/ui/semantic-validator-handoff/exceptions",
        "authority": _authority(),
        "source_timeline_event": event,
        "summary_line": f"{experiment_id} · {stage} · {kind} · {priority} · execute=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get(k))
        for k in (
            "experiment_id",
            "gap_id",
            "gap_kind",
            "gap_state",
            "priority",
            "severity",
            "stage",
            "event_state",
            "operator_action",
            "summary_line",
        )
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    parts.extend(_as_list(row.get("operator_checklist")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    gap_kind: set[str],
    gap_state: set[str],
    priority: set[str],
    severity: set[str],
    stage: set[str],
    include_resolved: bool,
) -> bool:
    if bool(row.get("resolved")) and not include_resolved:
        return False
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    return not (
        (gap_kind and _norm(row.get("gap_kind")) not in gap_kind)
        or (gap_state and _norm(row.get("gap_state")) not in gap_state)
        or (priority and _norm(row.get("priority")) not in priority)
        or (severity and _norm(row.get("severity")) not in severity)
        or (stage and _norm(row.get("stage")) not in stage)
    )


__all__ = ["_classify", "_repair_route", "_checklist", "_gap_row", "_haystack", "_matches"]
