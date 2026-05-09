"""Checklist item synthesis and filtering for semantic validator handoff clearance."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_clearance_checklist_common import (
    _CHECK_STATE_RANK,
    _POSTURE_RANK,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _SEVERITY_RANK,
    _as_list,
    _authority,
    _contains,
    _digest,
    _norm,
    _s,
)


def _instruction(check_state: str, dossier: dict[str, Any], check: dict[str, Any]) -> str:
    check_id = _s(check.get("check_id")) or "unknown_check"
    if check_state == "BLOCKED":
        return f"Resolve blocker {check_id} outside this read-plane, then refresh the clearance dossier and checklist."
    if check_state == "WAITING_EXTERNAL_ARTIFACT":
        return f"Collect the external evidence for {check_id} outside this read-plane, then refresh the source surfaces."
    if check_state == "ATTENTION_REQUIRED":
        return f"Review {check_id} through the source route; this checklist cannot acknowledge, override, approve, or sign off."
    return f"{check_id} is observed as pass in this projection; this is not approval, signoff, or clearance."


def _checklist_item(
    dossier: dict[str, Any],
    check: dict[str, Any],
    *,
    dossier_index: int,
    check_index: int,
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    check_state = _s(check.get("check_state")) or "UNKNOWN"
    check_id = _s(check.get("check_id")) or f"check_{check_index}"
    item_id = "semantic-validator-handoff-clearance-checklist-" + _digest(
        {
            "schema_version": _SCHEMA_VERSION,
            "clearance_dossier_id": dossier.get("clearance_dossier_id"),
            "check_id": check_id,
            "check_state": check_state,
            "source_schema_version": source_payload.get("schema_version"),
        }
    )[:20]
    attention_required = check_state != "PASS"
    waiting_external = check_state == "WAITING_EXTERNAL_ARTIFACT" or bool(dossier.get("requires_external_artifact")) and check_id == "external_artifact_gap_absent"
    blocked = check_state == "BLOCKED" or (check_state == "ATTENTION_REQUIRED" and bool(dossier.get("handoff_clearance_blocked")))
    route = _s(check.get("route")) or _s(dossier.get("routes", {}).get("clearance_dossier")) or "/ui/semantic-validator-handoff/clearance-dossier"
    return {
        "checklist_item_id": item_id,
        "schema_version": _SCHEMA_VERSION,
        "ordinal": (dossier_index * 1000) + check_index,
        "dossier_ordinal": dossier.get("ordinal"),
        "check_ordinal": check_index,
        "check_id": check_id,
        "check_state": check_state,
        "check_rank": _CHECK_STATE_RANK.get(_norm(check_state), 99),
        "attention_required": attention_required,
        "blocks_clearance": blocked,
        "requires_external_artifact": waiting_external,
        "write_allowed": False,
        "clearance_dossier_id": dossier.get("clearance_dossier_id"),
        "clearance_gate_id": dossier.get("clearance_gate_id"),
        "review_posture": dossier.get("review_posture"),
        "clearance_status": dossier.get("clearance_status"),
        "scope_key": dossier.get("scope_key"),
        "experiment_id": dossier.get("experiment_id"),
        "continuity_id": dossier.get("continuity_id"),
        "chain_id": dossier.get("chain_id"),
        "chain_digest": dossier.get("chain_digest"),
        "audit_packet_id": dossier.get("audit_packet_id"),
        "audit_packet_digest": dossier.get("audit_packet_digest"),
        "priority": dossier.get("priority") or "P3",
        "severity": dossier.get("severity") or "INFO",
        "trust_banner": dossier.get("trust_banner") or "TRUSTED",
        "owner_hint": dossier.get("owner_hint") or "human_operator_clearance_owner",
        "evidence": _s(check.get("evidence")),
        "route": route,
        "operator_instruction": _instruction(check_state, dossier, check),
        "issue_codes": _as_list(dossier.get("issue_codes")),
        "issue_count": int(dossier.get("issue_count") or len(_as_list(dossier.get("issue_codes")))),
        "phase_set": _as_list(dossier.get("phase_set")),
        "dossier_digest": dossier.get("dossier_digest"),
        "authority": _authority(),
        "check_acknowledgment_authority": "none_read_plane",
        "check_override_authority": "none_read_plane",
        "clearance_decision_authority": "none_read_plane",
        "operator_approval_authority": "none_read_plane",
        "signoff_authority": "none_read_plane",
        "dossier_materialization_authority": "none_read_plane",
        "resolution_step_acknowledgment_authority": "none_read_plane",
        "repair_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_review_check": check,
        "source_clearance_dossier": dossier,
        "summary_line": f"{(dossier_index * 1000) + check_index}. {check_state} · {check_id} · {dossier.get('experiment_id') or dossier.get('scope_key')} · ack=false override=false approve=false signoff=false execute=false",
    }


def _items_from_dossiers(dossiers: list[dict[str, Any]], source_payload: dict[str, Any]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for dossier_index, dossier in enumerate(dossiers, start=1):
        checks = [check for check in dossier.get("review_checks", []) if isinstance(check, dict)]
        for check_index, check in enumerate(checks, start=1):
            items.append(
                _checklist_item(
                    dossier,
                    check,
                    dossier_index=dossier_index,
                    check_index=check_index,
                    source_payload=source_payload,
                )
            )
    return items


def _sort_item(item: dict[str, Any]) -> tuple[Any, ...]:
    return (
        int(item.get("check_rank") if item.get("check_rank") is not None else 99),
        _POSTURE_RANK.get(_norm(item.get("review_posture")), 99),
        _PRIORITY_RANK.get(_norm(item.get("priority")), 9),
        _SEVERITY_RANK.get(_norm(item.get("severity")), 9),
        _s(item.get("experiment_id")),
        _s(item.get("clearance_dossier_id")),
        int(item.get("check_ordinal") or 0),
    )


def _haystack(item: dict[str, Any]) -> str:
    return "\n".join(
        [
            _s(item.get("checklist_item_id")),
            _s(item.get("check_id")),
            _s(item.get("check_state")),
            _s(item.get("review_posture")),
            _s(item.get("clearance_status")),
            _s(item.get("clearance_dossier_id")),
            _s(item.get("clearance_gate_id")),
            _s(item.get("scope_key")),
            _s(item.get("experiment_id")),
            _s(item.get("priority")),
            _s(item.get("severity")),
            _s(item.get("trust_banner")),
            _s(item.get("owner_hint")),
            _s(item.get("evidence")),
            _s(item.get("operator_instruction")),
            _s(item.get("summary_line")),
        ]
        + _as_list(item.get("issue_codes"))
        + _as_list(item.get("phase_set"))
    )


def _matches(
    item: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    check_id_contains: str | None,
    check_state: set[str],
    review_posture: set[str],
    clearance_status: set[str],
    priority: set[str],
    severity: set[str],
    trust_banner: set[str],
    owner_hint: set[str],
    attention_required: bool | None,
    blocks_clearance: bool | None,
    requires_external_artifact: bool | None,
) -> bool:
    return (
        _contains(item.get("experiment_id"), experiment_id_contains)
        and (not issue_contains or _contains(_haystack(item), issue_contains))
        and _contains(item.get("check_id"), check_id_contains)
        and (not check_state or _norm(item.get("check_state")) in check_state)
        and (not review_posture or _norm(item.get("review_posture")) in review_posture)
        and (not clearance_status or _norm(item.get("clearance_status")) in clearance_status)
        and (not priority or _norm(item.get("priority")) in priority)
        and (not severity or _norm(item.get("severity")) in severity)
        and (not trust_banner or _norm(item.get("trust_banner")) in trust_banner)
        and (not owner_hint or _norm(item.get("owner_hint")) in owner_hint)
        and (attention_required is None or bool(item.get("attention_required")) is attention_required)
        and (blocks_clearance is None or bool(item.get("blocks_clearance")) is blocks_clearance)
        and (requires_external_artifact is None or bool(item.get("requires_external_artifact")) is requires_external_artifact)
    )


def _degraded(source_payload: dict[str, Any], filtered: list[dict[str, Any]]) -> list[str]:
    degraded: list[str] = []
    if _as_list(source_payload.get("degraded")):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_DOSSIER_DEGRADED")
    if any(item.get("blocks_clearance") for item in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_BLOCKED")
    if any(item.get("requires_external_artifact") for item in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_WAITING_EXTERNAL_ARTIFACT")
    if any(item.get("attention_required") for item in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLEARANCE_CHECKLIST_ATTENTION_REQUIRED")
    return degraded
