"""Row synthesis for semantic validator handoff remediation read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_remediation_common import (
    _COMPONENT_FIELDS,
    _COMPONENT_LABELS,
    _LINK_STEP_TEMPLATES,
    _READY_ACTION,
    _REMEDIATE_ACTION,
    _SEVERITY_RANK,
    _STEP_LIBRARY,
    _as_list,
    _contains,
    _link_digest,
    _s,
)


def _step_template(issue_code: str) -> dict[str, str]:
    if issue_code in _STEP_LIBRARY:
        return dict(_STEP_LIBRARY[issue_code])
    for suffix, template in _LINK_STEP_TEMPLATES:
        if issue_code.endswith(suffix):
            return dict(template)
    return {
        "severity": "MEDIUM",
        "target_component": "component_set",
        "operator_action": "INVESTIGATE_LINEAGE_OR_COMPONENT_ISSUE",
        "repair_hint": "Inspect the source artifact summaries and verifier output for this issue code, then regenerate only from canonical upstream inputs.",
        "rationale": "The issue is not mapped to a specialized repair step, but still blocks automated readiness claims.",
    }


def _issue_step(issue_code: str, *, chain: dict[str, Any], index: int) -> dict[str, Any]:
    template = _step_template(issue_code)
    return {
        "step_id": f"{chain.get('chain_id')}:step-{index:03d}",
        "issue_code": issue_code,
        "severity": template["severity"],
        "target_component": template["target_component"],
        "operator_action": template["operator_action"],
        "repair_hint": template["repair_hint"],
        "rationale": template["rationale"],
        "mutation_authority": "none_read_plane_external_operator_workflow_required",
        "validator_submission_authority": "none_read_plane",
    }


def _max_severity(steps: list[dict[str, Any]]) -> str:
    if not steps:
        return "NONE"
    return max((_s(step.get("severity")) or "MEDIUM" for step in steps), key=lambda v: _SEVERITY_RANK.get(v, 2))


def _missing_components(issue_codes: list[str]) -> list[str]:
    missing: list[str] = []
    for issue_code in issue_codes:
        if not issue_code.startswith("MISSING_"):
            continue
        key = issue_code.removeprefix("MISSING_")
        missing.append(_COMPONENT_FIELDS.get(key, key.lower()))
    return missing


def _component_labels_for_missing(missing: list[str]) -> list[str]:
    reverse = {v: k for k, v in _COMPONENT_FIELDS.items()}
    labels: list[str] = []
    for component in missing:
        key = reverse.get(component, component.upper())
        labels.append(_COMPONENT_LABELS.get(key, component))
    return labels


def _broken_link_codes(issue_codes: list[str]) -> list[str]:
    return [code for code in issue_codes if code.endswith("ID_LINK_BROKEN") or code.endswith("PAYLOAD_CHECKSUM_MISMATCH")]


def _remediation_status(chain: dict[str, Any], steps: list[dict[str, Any]]) -> str:
    if not steps and bool(chain.get("ready_for_operator_review")):
        return "READY_NO_ACTION"
    issue_codes = _as_list(chain.get("issue_codes"))
    if any(code.startswith("MISSING_") for code in issue_codes):
        return "LINEAGE_RECONSTRUCTION_REQUIRED"
    if _broken_link_codes(issue_codes):
        return "EVIDENCE_REPAIR_REQUIRED"
    return "ACTION_REQUIRED"


def _priority_score(status: str, severity: str, steps: list[dict[str, Any]]) -> int:
    if status == "READY_NO_ACTION":
        return 0
    return min(999, _SEVERITY_RANK.get(severity, 2) * 100 + len(steps) * 10)


def _chain_haystack(row: dict[str, Any]) -> str:
    parts = [
        str(row.get("remediation_status") or ""),
        str(row.get("severity") or ""),
        str(row.get("recommended_action") or ""),
        str(row.get("summary_line") or ""),
    ]
    parts.extend(_as_list(row.get("issue_codes")))
    parts.extend(_as_list(row.get("warning_codes")))
    parts.extend(str(step.get("operator_action") or "") for step in row.get("remediation_steps") or [])
    return "\n".join(parts)


def _build_remediation_record(chain: dict[str, Any]) -> dict[str, Any]:
    issue_codes = list(dict.fromkeys(_as_list(chain.get("issue_codes"))))
    steps = [_issue_step(issue_code, chain=chain, index=index) for index, issue_code in enumerate(issue_codes, start=1)]
    severity = _max_severity(steps)
    status = _remediation_status(chain, steps)
    operator_action_required = status != "READY_NO_ACTION"
    validator_ingress_blocked = operator_action_required or not bool(chain.get("ready_for_validator_ingress"))
    missing = _missing_components(issue_codes)
    broken_links = _broken_link_codes(issue_codes)
    remediation_id = "semantic-validator-remediation-" + _link_digest(
        [chain.get("chain_id"), chain.get("chain_digest"), *issue_codes]
    )[:20]
    action = _READY_ACTION if not operator_action_required else _REMEDIATE_ACTION
    priority = _priority_score(status, severity, steps)
    return {
        "remediation_id": remediation_id,
        "chain_id": chain.get("chain_id"),
        "chain_digest": chain.get("chain_digest"),
        "experiment_id": chain.get("experiment_id"),
        "chain_status": chain.get("status"),
        "remediation_status": status,
        "severity": severity,
        "priority_score": priority,
        "operator_action_required": operator_action_required,
        "validator_ingress_blocked": validator_ingress_blocked,
        "ready_for_operator_review": bool(chain.get("ready_for_operator_review")),
        "ready_for_validator_ingress": bool(chain.get("ready_for_validator_ingress")),
        "recommended_action": action,
        "issue_count": len(issue_codes),
        "issue_codes": issue_codes,
        "warning_codes": _as_list(chain.get("warning_codes")),
        "missing_components": missing,
        "missing_component_labels": _component_labels_for_missing(missing),
        "broken_link_codes": broken_links,
        "component_blocker_codes": _as_list(chain.get("component_blocker_codes")),
        "component_issue_codes": _as_list(chain.get("component_issue_codes")),
        "remediation_step_count": len(steps),
        "remediation_steps": steps,
        "link_checks": list(chain.get("link_checks") or []),
        "components": dict(chain.get("components") or {}),
        "summary_line": f"{chain.get('experiment_id')} · {status} · severity={severity} · steps={len(steps)}",
    }


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    chain_status: set[str],
    remediation_status: set[str],
    severity: set[str],
    require_operator_action: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_chain_haystack(row), issue_contains):
        return False
    if chain_status and _s(row.get("chain_status")).upper() not in chain_status:
        return False
    if remediation_status and _s(row.get("remediation_status")).upper() not in remediation_status:
        return False
    if severity and _s(row.get("severity")).upper() not in severity:
        return False
    if require_operator_action is not None and bool(row.get("operator_action_required")) is not require_operator_action:
        return False
    return True
