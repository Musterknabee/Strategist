"""Runbook card synthesis and filtering for semantic validator handoff runbook."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_runbook_common import (
    _as_list,
    _authority,
    _contains,
    _norm,
    _s,
)


def _template_fields(template: object) -> list[str]:
    if not isinstance(template, dict):
        return []
    fields: list[str] = []
    for key, value in template.items():
        if isinstance(value, str) and ("<REQUIRED" in value.upper() or "<PENDING" in value.upper()):
            fields.append(str(key))
    return sorted(fields)


def _first_issue(row: dict[str, Any]) -> str:
    issues = _as_list(row.get("issue_codes"))
    return issues[0] if issues else "NO_ISSUE_CODE"


def _checklist(action_kind: str, row: dict[str, Any]) -> list[str]:
    if action_kind == "CREATE_EXTERNAL_CLOSURE_ATTESTATION":
        fields = _template_fields(row.get("closure_template"))
        field_text = ", ".join(fields) if fields else "required attestation fields"
        return [
            "Copy the closure attestation template from the selected continuity row.",
            f"Fill externally controlled human fields: {field_text}.",
            "Keep closure_packet_digest unchanged and verify it matches the continuity row.",
            "Store the attestation as external evidence under artifacts; then refresh this read-plane.",
        ]
    if action_kind == "REPAIR_CLOSURE_ATTESTATION":
        return [
            "Open the selected closure row and inspect matched closure attestations.",
            "Compare closure_packet_digest against the deterministic closure packet digest.",
            "Replace placeholder or mismatched human fields in a new external attestation artifact.",
            "Refresh closure and continuity read-planes after the external artifact is present.",
        ]
    if action_kind == "VERIFY_ARCHIVE_MANIFEST":
        return [
            "Open the archive manifest route for this handoff chain.",
            "Verify archive_packet_digest and artifact inventory continuity before closure.",
            "Create or repair the external archive manifest outside this read-plane if required.",
            "Return to closure once archive status is ARCHIVE_MANIFEST_VERIFIED.",
        ]
    if action_kind == "RESTORE_MISSING_STAGE_EVIDENCE":
        return [
            "Inspect the stage path and identify the first missing or not-ready stage.",
            "Return to that stage route and restore the missing upstream evidence artifact externally.",
            "Refresh the continuity cockpit and confirm all prerequisite stages are present.",
        ]
    if action_kind == "RETAIN_AUDIT_TRAIL":
        return [
            "Retain the recorded closure attestation and its digest chain as audit evidence.",
            "Do not treat closed handoff continuity as promotion, adjudication, or live execution authority.",
            "Use downstream release governance only if a separate governed process requires it.",
        ]
    return [
        "Inspect the selected continuity row and source route.",
        "Resolve open evidence issues outside this read-plane.",
        "Refresh the semantic-validator handoff continuity cockpit.",
    ]


def _runbook_decision(row: dict[str, Any]) -> tuple[str, str, str, str]:
    terminal = _s(row.get("terminal_status"))
    closure_status = _s(row.get("closure_status"))
    current_stage = _s(row.get("current_stage")) or "unknown"
    issues = set(_as_list(row.get("issue_codes")))
    if terminal == "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION":
        return ("RETAIN_AUDIT_TRAIL", "P4", "INFO", "closed")
    if terminal in {"BLOCKED_INVALID_CLOSURE_ATTESTATION"} or closure_status in {
        "CLOSURE_ATTESTATION_INVALID",
        "CLOSURE_ATTESTATION_DIGEST_MISMATCH",
    }:
        return ("REPAIR_CLOSURE_ATTESTATION", "P0", "BLOCKED", current_stage)
    if "ARCHIVE_MANIFEST_NOT_VERIFIED" in issues or closure_status == "BLOCKED_ARCHIVE_NOT_VERIFIED":
        return ("VERIFY_ARCHIVE_MANIFEST", "P0", "BLOCKED", "archive")
    if terminal == "PARTIAL_CHAIN_MISSING_STAGE_EVIDENCE":
        return ("RESTORE_MISSING_STAGE_EVIDENCE", "P0", "BLOCKED", current_stage)
    if terminal == "AWAITING_EXTERNAL_CLOSURE_ATTESTATION" or bool(row.get("external_artifact_required")):
        return ("CREATE_EXTERNAL_CLOSURE_ATTESTATION", "P1", "WARN", "closure")
    if bool(row.get("open_action")):
        return (_s(row.get("recommended_action")) or "INSPECT_CONTINUITY_ROW", "P2", "WARN", current_stage)
    return ("RETAIN_AUDIT_TRAIL", "P4", "INFO", current_stage)


def _runbook_card(row: dict[str, Any]) -> dict[str, Any]:
    action_kind, priority, severity, stage = _runbook_decision(row)
    completed = action_kind == "RETAIN_AUDIT_TRAIL" and not bool(row.get("open_action"))
    source_route = _s(row.get("source_route")) or "/ui/semantic-validator-handoff/continuity"
    next_route = {
        "archive": "/ui/semantic-validator-handoff/archive",
        "closure": "/ui/semantic-validator-handoff/closure",
        "closed": "/ui/semantic-validator-handoff/continuity",
    }.get(stage, source_route)
    first_issue = _first_issue(row)
    return {
        "runbook_card_id": f"semantic-validator-handoff-runbook-{row.get('experiment_id') or row.get('continuity_id') or 'UNKNOWN'}-{action_kind}",
        "continuity_id": row.get("continuity_id"),
        "experiment_id": row.get("experiment_id"),
        "chain_id": row.get("chain_id"),
        "chain_digest": row.get("chain_digest"),
        "closure_gate_id": row.get("closure_gate_id"),
        "archive_gate_id": row.get("archive_gate_id"),
        "decision_id": row.get("decision_id"),
        "terminal_status": row.get("terminal_status"),
        "closure_status": row.get("closure_status"),
        "current_stage": row.get("current_stage"),
        "action_kind": action_kind,
        "priority": priority,
        "severity": severity,
        "completed": completed,
        "blocked": severity == "BLOCKED",
        "external_artifact_required": bool(row.get("external_artifact_required")),
        "next_external_artifact_kind": row.get("next_external_art_kind") or row.get("next_external_artifact_kind"),
        "next_external_schema_version": row.get("next_external_schema_version"),
        "required_template_fields": _template_fields(row.get("closure_template")),
        "first_issue_code": first_issue,
        "issue_codes": _as_list(row.get("issue_codes")),
        "issue_count": len(_as_list(row.get("issue_codes"))),
        "stage_count_expected": row.get("stage_count_expected"),
        "stage_count_present": row.get("stage_count_present"),
        "ready_stage_count": row.get("ready_stage_count"),
        "closure_packet_digest": row.get("closure_packet_digest"),
        "recommended_action": row.get("recommended_action") or action_kind,
        "operator_action": action_kind.replace("_", " ").capitalize(),
        "checklist": _checklist(action_kind, row),
        "source_route": source_route,
        "next_route": next_route,
        "continuity_route": row.get("continuity_route") or "/ui/semantic-validator-handoff/continuity",
        "authority": _authority(),
        "source_continuity_row": row,
        "summary_line": f"{row.get('experiment_id')} · {priority} · {action_kind} · execute=false",
    }


def _haystack(card: dict[str, Any]) -> str:
    parts = [
        _s(card.get("experiment_id")),
        _s(card.get("terminal_status")),
        _s(card.get("closure_status")),
        _s(card.get("action_kind")),
        _s(card.get("priority")),
        _s(card.get("severity")),
        _s(card.get("first_issue_code")),
        _s(card.get("summary_line")),
    ]
    parts.extend(_as_list(card.get("issue_codes")))
    parts.extend(_as_list(card.get("checklist")))
    return "\n".join(parts)


def _matches(
    card: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    action_kind: set[str],
    priority: set[str],
    severity: set[str],
    completed: bool | None,
) -> bool:
    if not _contains(card.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(card), issue_contains):
        return False
    if action_kind and _norm(card.get("action_kind")) not in action_kind:
        return False
    if priority and _norm(card.get("priority")) not in priority:
        return False
    if severity and _norm(card.get("severity")) not in severity:
        return False
    if completed is not None and bool(card.get("completed")) is not completed:
        return False
    return True
