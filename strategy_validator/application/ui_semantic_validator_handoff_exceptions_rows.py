"""Exception-row synthesis and filtering for semantic validator handoff read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_exceptions_common import (
    _as_list,
    _authority,
    _contains,
    _norm,
    _s,
)


def _exception_kind(card: dict[str, Any]) -> str:
    action = _s(card.get("action_kind"))
    first_issue = _s(card.get("first_issue_code"))
    if bool(card.get("blocked")) or _s(card.get("priority")) == "P0":
        if "DIGEST" in first_issue or "ATTESTATION" in action:
            return "BLOCKED_INTEGRITY_EXCEPTION"
        return "BLOCKED_HANDOFF_EXCEPTION"
    if bool(card.get("external_artifact_required")):
        return "EXTERNAL_ARTIFACT_REQUIRED_EXCEPTION"
    if _s(card.get("severity")) == "WARN":
        return "OPERATOR_REVIEW_EXCEPTION"
    return "AUDIT_RETENTION_NOTE"


def _exception_state(card: dict[str, Any]) -> str:
    if bool(card.get("completed")):
        return "RESOLVED_AUDIT_RETENTION"
    if bool(card.get("blocked")) or _s(card.get("priority")) == "P0":
        return "BLOCKED"
    if bool(card.get("external_artifact_required")):
        return "AWAITING_EXTERNAL_ARTIFACT"
    return "OPEN_REVIEW"


def _escalation_lane(card: dict[str, Any], state: str) -> str:
    if state == "BLOCKED":
        return "operator_integrity_repair"
    if state == "AWAITING_EXTERNAL_ARTIFACT":
        return "operator_external_attestation"
    if state == "RESOLVED_AUDIT_RETENTION":
        return "audit_retention"
    return "operator_review"


def _exception_row(card: dict[str, Any]) -> dict[str, Any]:
    state = _exception_state(card)
    kind = _exception_kind(card)
    issue_codes = _as_list(card.get("issue_codes"))
    exception_id = (
        f"semantic-validator-handoff-exception-"
        f"{card.get('experiment_id') or card.get('runbook_card_id') or 'UNKNOWN'}-{kind}"
    )
    return {
        "exception_id": exception_id,
        "runbook_card_id": card.get("runbook_card_id"),
        "continuity_id": card.get("continuity_id"),
        "experiment_id": card.get("experiment_id"),
        "chain_id": card.get("chain_id"),
        "chain_digest": card.get("chain_digest"),
        "closure_gate_id": card.get("closure_gate_id"),
        "archive_gate_id": card.get("archive_gate_id"),
        "decision_id": card.get("decision_id"),
        "terminal_status": card.get("terminal_status"),
        "closure_status": card.get("closure_status"),
        "current_stage": card.get("current_stage"),
        "exception_kind": kind,
        "exception_state": state,
        "priority": card.get("priority"),
        "severity": card.get("severity"),
        "blocked": bool(card.get("blocked")),
        "completed": bool(card.get("completed")),
        "external_artifact_required": bool(card.get("external_artifact_required")),
        "next_external_artifact_kind": card.get("next_external_artifact_kind"),
        "next_external_schema_version": card.get("next_external_schema_version"),
        "first_issue_code": card.get("first_issue_code") or "NO_ISSUE_CODE",
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "action_kind": card.get("action_kind"),
        "operator_action": card.get("operator_action"),
        "checklist": _as_list(card.get("checklist")),
        "required_template_fields": _as_list(card.get("required_template_fields")),
        "escalation_lane": _escalation_lane(card, state),
        "next_route": card.get("next_route") or "/ui/semantic-validator-handoff/runbook",
        "source_route": "/ui/semantic-validator-handoff/runbook",
        "runbook_route": "/ui/semantic-validator-handoff/runbook",
        "continuity_route": card.get("continuity_route") or "/ui/semantic-validator-handoff/continuity",
        "closure_packet_digest": card.get("closure_packet_digest"),
        "authority": _authority(),
        "source_runbook_card": card,
        "summary_line": f"{card.get('experiment_id')} · {state} · {kind} · execute=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("experiment_id")),
        _s(row.get("exception_kind")),
        _s(row.get("exception_state")),
        _s(row.get("priority")),
        _s(row.get("severity")),
        _s(row.get("first_issue_code")),
        _s(row.get("action_kind")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    parts.extend(_as_list(row.get("checklist")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    exception_state: set[str],
    exception_kind: set[str],
    priority: set[str],
    severity: set[str],
    include_resolved: bool,
) -> bool:
    if not include_resolved and bool(row.get("completed")):
        return False
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if exception_state and _norm(row.get("exception_state")) not in exception_state:
        return False
    if exception_kind and _norm(row.get("exception_kind")) not in exception_kind:
        return False
    if priority and _norm(row.get("priority")) not in priority:
        return False
    if severity and _norm(row.get("severity")) not in severity:
        return False
    return True
