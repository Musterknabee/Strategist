"""Continuity row synthesis for semantic validator handoff closure chains."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_continuity_common import (
    _STAGES,
    _as_list,
    _authority,
    _contains,
    _norm,
    _s,
)


def _stage_record(closure: dict[str, Any], stage: str, label: str, route: str) -> dict[str, Any]:
    id_fields = {
        "decision": "decision_id",
        "signoff": "signoff_gate_id",
        "custody": "custody_gate_id",
        "archive": "archive_gate_id",
        "closure": "closure_gate_id",
    }
    digest_fields = {
        "decision": "decision_packet_digest",
        "signoff": "decision_packet_digest",
        "custody": "custody_packet_digest",
        "archive": "archive_packet_digest",
        "closure": "closure_packet_digest",
    }
    status = closure.get("closure_status") if stage == "closure" else (
        closure.get("archive_status") if stage == "archive" else "PRESENT"
    )
    record_id = closure.get(id_fields[stage])
    present = bool(_s(record_id))
    issues: list[str] = []
    if not present:
        issues.append(f"{stage.upper()}_EVIDENCE_MISSING")
    if stage == "closure":
        issues.extend(_as_list(closure.get("issue_codes")))
    if stage == "archive" and _s(closure.get("archive_status")) != "ARCHIVE_MANIFEST_VERIFIED":
        issues.append("ARCHIVE_MANIFEST_NOT_VERIFIED")
    return {
        "stage": stage,
        "label": label,
        "route": route,
        "record_id": record_id,
        "status": status,
        "present": present,
        "digest": closure.get(digest_fields[stage]),
        "issue_codes": list(dict.fromkeys(issues)),
        "issue_count": len(set(issues)),
        "ready": present and not issues,
    }


def _terminal_status(closure: dict[str, Any], stages: list[dict[str, Any]]) -> str:
    closure_status = _s(closure.get("closure_status"))
    if closure_status == "CLOSURE_ATTESTATION_RECORDED" and all(stage.get("ready") for stage in stages[:-1]):
        return "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION"
    if closure_status == "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION":
        return "AWAITING_EXTERNAL_CLOSURE_ATTESTATION"
    if closure_status in {"CLOSURE_ATTESTATION_INVALID", "CLOSURE_ATTESTATION_DIGEST_MISMATCH"}:
        return "BLOCKED_INVALID_CLOSURE_ATTESTATION"
    if any(not stage.get("present") for stage in stages):
        return "PARTIAL_CHAIN_MISSING_STAGE_EVIDENCE"
    return "BLOCKED_BEFORE_CLOSURE"


def _current_stage(stages: list[dict[str, Any]]) -> str:
    for stage in stages:
        if not stage.get("ready"):
            return str(stage.get("stage") or "unknown")
    return "closure"


def _continuity_row(closure: dict[str, Any]) -> dict[str, Any]:
    stages = [_stage_record(closure, *spec) for spec in _STAGES]
    terminal = _terminal_status(closure, stages)
    current = _current_stage(stages)
    issue_codes = list(dict.fromkeys(code for stage in stages for code in _as_list(stage.get("issue_codes"))))
    open_action = terminal != "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION"
    external_required = _s(closure.get("closure_status")) == "READY_FOR_EXTERNAL_CLOSURE_ATTESTATION"
    return {
        "continuity_id": f"semantic-validator-continuity-{closure.get('experiment_id') or closure.get('closure_gate_id') or 'UNKNOWN'}",
        "experiment_id": closure.get("experiment_id"),
        "terminal_status": terminal,
        "current_stage": current,
        "severity": "INFO" if not open_action else ("BLOCKED" if terminal.startswith("BLOCKED") else "WARN"),
        "trust_banner": closure.get("trust_banner") or "TRUST_RESTRICTED",
        "chain_id": closure.get("chain_id"),
        "chain_digest": closure.get("chain_digest"),
        "closure_gate_id": closure.get("closure_gate_id"),
        "closure_status": closure.get("closure_status"),
        "closure_attestation_recorded": bool(closure.get("closure_attestation_recorded")),
        "closure_attestation_required": bool(closure.get("closure_attestation_required")),
        "closure_attestation_id": closure.get("closure_attestation_id"),
        "closure_packet_digest": closure.get("closure_packet_digest"),
        "archive_gate_id": closure.get("archive_gate_id"),
        "archive_manifest_id": closure.get("archive_manifest_id"),
        "custody_gate_id": closure.get("custody_gate_id"),
        "signoff_gate_id": closure.get("signoff_gate_id"),
        "decision_id": closure.get("decision_id"),
        "issue_codes": issue_codes,
        "issue_count": len(issue_codes),
        "stage_count_expected": len(stages),
        "stage_count_present": sum(1 for stage in stages if stage.get("present")),
        "ready_stage_count": sum(1 for stage in stages if stage.get("ready")),
        "open_action": open_action,
        "external_artifact_required": external_required,
        "next_external_artifact_kind": "semantic_validator_handoff_closure_attestation" if external_required else None,
        "next_external_schema_version": "semantic_validator_handoff_closure_attestation/v1" if external_required else None,
        "closure_template": closure.get("closure_template") if external_required else None,
        "recommended_action": closure.get("recommended_action"),
        "authority": _authority(),
        "stage_path": stages,
        "source_route": "/ui/semantic-validator-handoff/closure",
        "continuity_route": "/ui/semantic-validator-handoff/continuity",
        "summary_line": f"{closure.get('experiment_id')} · {terminal} · stage={current} · execute=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [_s(row.get(k)) for k in ("experiment_id", "terminal_status", "current_stage", "closure_status", "recommended_action", "summary_line")]
    parts.extend(_as_list(row.get("issue_codes")))
    for stage in row.get("stage_path") or []:
        if isinstance(stage, dict):
            parts.extend([_s(stage.get("stage")), _s(stage.get("status")), _s(stage.get("record_id"))])
            parts.extend(_as_list(stage.get("issue_codes")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    terminal_status: set[str],
    current_stage: set[str],
    open_action: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if terminal_status and _norm(row.get("terminal_status")) not in terminal_status:
        return False
    if current_stage and _norm(row.get("current_stage")) not in current_stage:
        return False
    if open_action is not None and bool(row.get("open_action")) is not open_action:
        return False
    return True
