"""Row synthesis and filtering for semantic validator handoff review read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_review_common import (
    _BLOCKED_ACTION,
    _COMPONENT_LABELS,
    _READY_ACTION,
    _STACKED_CHECKS,
    _as_list,
    _contains,
    _digest,
    _s,
)


def _component_paths(components: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for key in ("decision_ledger", "handoff_certificate", "validator_packet", "ingress_certificate"):
        component = components.get(key)
        rows.append(
            {
                "component": key,
                "label": _COMPONENT_LABELS[key],
                "present": component is not None,
                "artifact_id": None if component is None else component.get("artifact_id"),
                "payload_checksum": None if component is None else component.get("payload_checksum"),
                "artifact_sha256": None if component is None else component.get("artifact_sha256"),
                "artifact_path": None if component is None else component.get("artifact_path"),
                "verified": bool(component.get("verified")) if component is not None else False,
                "handoff_allowed": bool(component.get("handoff_allowed")) if component is not None else False,
                "ready_for_validator_ingress": component.get("ready_for_validator_ingress") if component is not None else None,
            }
        )
    return rows


def _check_status(*, ok: bool, issue_codes: list[str], blocker_codes: list[str] | None = None) -> str:
    if ok:
        return "PASS"
    if blocker_codes:
        return "BLOCK"
    if issue_codes:
        return "BLOCK"
    return "BLOCK"


def _review_checklist(row: dict[str, Any]) -> list[dict[str, Any]]:
    components: dict[str, Any] = dict(row.get("components") or {})
    component_paths = _component_paths(components)
    issue_codes = _as_list(row.get("issue_codes"))
    component_blockers = _as_list(row.get("component_blocker_codes"))
    component_issues = _as_list(row.get("component_issue_codes"))
    broken_link_codes = _as_list(row.get("broken_link_codes"))
    remediation_steps = list(row.get("remediation_steps") or [])

    component_complete = all(item["present"] for item in component_paths)
    lineage_clear = not broken_link_codes and _s(row.get("chain_status")) == "READY"
    component_clear = not component_blockers and not component_issues and not any(
        code in issue_codes for code in ("COMPONENT_BLOCKERS_PRESENT", "COMPONENT_SELF_VERIFICATION_ISSUES_PRESENT", "UNVERIFIED_COMPONENTS_PRESENT")
    )
    handoff_clear = not any(code == "HANDOFF_NOT_ALLOWED_FOR_ALL_PRESENT_COMPONENTS" for code in issue_codes)
    ingress_ready = bool(row.get("ready_for_validator_ingress")) and not bool(row.get("validator_ingress_blocked"))
    remediation_clear = _s(row.get("remediation_status")) == "READY_NO_ACTION" and not remediation_steps

    status_by_check = {
        "component_chain_complete": component_complete,
        "lineage_integrity_clear": lineage_clear,
        "component_verification_clear": component_clear,
        "handoff_allowed_clear": handoff_clear,
        "validator_ingress_ready": ingress_ready,
        "remediation_clear": remediation_clear,
    }
    issue_refs = {
        "component_chain_complete": _as_list(row.get("missing_components")),
        "lineage_integrity_clear": broken_link_codes,
        "component_verification_clear": sorted(dict.fromkeys(component_blockers + component_issues)),
        "handoff_allowed_clear": [code for code in issue_codes if code == "HANDOFF_NOT_ALLOWED_FOR_ALL_PRESENT_COMPONENTS"],
        "validator_ingress_ready": [code for code in issue_codes if code == "INGRESS_CERTIFICATE_NOT_READY_FOR_VALIDATOR_INGRESS"],
        "remediation_clear": [step.get("issue_code") for step in remediation_steps if step.get("issue_code")],
    }

    checklist: list[dict[str, Any]] = []
    for spec in _STACKED_CHECKS:
        check_id = spec["check_id"]
        refs = [str(ref) for ref in issue_refs.get(check_id, []) if str(ref).strip()]
        passed = bool(status_by_check[check_id])
        checklist.append(
            {
                "check_id": check_id,
                "label": spec["label"],
                "requirement": spec["requirement"],
                "status": _check_status(ok=passed, issue_codes=refs, blocker_codes=refs),
                "issue_refs": refs,
                "evidence_ref": row.get("chain_id"),
                "detail": "pass" if passed else (", ".join(refs) if refs else "blocked by upstream lineage/remediation state"),
            }
        )
    return checklist


def _review_status(row: dict[str, Any], checklist: list[dict[str, Any]]) -> str:
    if all(check.get("status") == "PASS" for check in checklist) and not bool(row.get("operator_action_required")):
        return "READY_FOR_OPERATOR_REVIEW"
    status = _s(row.get("remediation_status"))
    if status in {"EVIDENCE_REPAIR_REQUIRED", "LINEAGE_RECONSTRUCTION_REQUIRED"}:
        return status
    return "REMEDIATION_REQUIRED"


def _trust_banner(review_status: str, row: dict[str, Any]) -> str:
    if review_status == "READY_FOR_OPERATOR_REVIEW":
        return "TRUSTED"
    if _s(row.get("severity")) in {"CRITICAL", "HIGH"}:
        return "UNTRUSTED"
    return "TRUST_RESTRICTED"


def _review_row(row: dict[str, Any]) -> dict[str, Any]:
    checklist = _review_checklist(row)
    review_status = _review_status(row, checklist)
    operator_review_allowed = review_status == "READY_FOR_OPERATOR_REVIEW"
    blocking_checks = [check for check in checklist if check.get("status") != "PASS"]
    component_paths = _component_paths(dict(row.get("components") or {}))
    review_id = "semantic-validator-review-" + _digest(
        [row.get("remediation_id"), row.get("chain_id"), row.get("chain_digest"), review_status]
    )[:20]
    return {
        "review_id": review_id,
        "remediation_id": row.get("remediation_id"),
        "chain_id": row.get("chain_id"),
        "chain_digest": row.get("chain_digest"),
        "experiment_id": row.get("experiment_id"),
        "chain_status": row.get("chain_status"),
        "remediation_status": row.get("remediation_status"),
        "severity": row.get("severity"),
        "review_status": review_status,
        "trust_banner": _trust_banner(review_status, row),
        "operator_review_allowed": operator_review_allowed,
        "validator_submission_allowed": False,
        "validator_submission_gate": "NOT_AUTHORIZED_BY_READ_PLANE",
        "promotion_allowed": False,
        "execution_allowed": False,
        "recommended_action": _READY_ACTION if operator_review_allowed else _BLOCKED_ACTION,
        "review_check_count": len(checklist),
        "review_pass_count": sum(1 for check in checklist if check.get("status") == "PASS"),
        "review_block_count": len(blocking_checks),
        "review_blocker_codes": sorted(
            dict.fromkeys(
                _as_list(row.get("issue_codes"))
                + _as_list(row.get("broken_link_codes"))
                + _as_list(row.get("component_blocker_codes"))
                + _as_list(row.get("component_issue_codes"))
            )
        ),
        "remediation_step_count": row.get("remediation_step_count", 0),
        "remediation_steps": list(row.get("remediation_steps") or []),
        "component_paths": component_paths,
        "component_count_present": sum(1 for component in component_paths if component.get("present")),
        "component_count_expected": len(component_paths),
        "review_checklist": checklist,
        "source_remediation": row,
        "summary_line": f"{row.get('experiment_id')} · {review_status} · checks={sum(1 for check in checklist if check.get('status') == 'PASS')}/{len(checklist)} · review_allowed={operator_review_allowed}",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("review_status")),
        _s(row.get("remediation_status")),
        _s(row.get("severity")),
        _s(row.get("recommended_action")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("review_blocker_codes")))
    for check in row.get("review_checklist") or []:
        parts.append(_s(check.get("check_id")))
        parts.append(_s(check.get("detail")))
        parts.extend(_as_list(check.get("issue_refs")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    review_status: set[str],
    operator_review_allowed: bool | None,
    trust_banner: set[str],
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if review_status and _s(row.get("review_status")).upper() not in review_status:
        return False
    if trust_banner and _s(row.get("trust_banner")).upper() not in trust_banner:
        return False
    if operator_review_allowed is not None and bool(row.get("operator_review_allowed")) is not operator_review_allowed:
        return False
    return True
