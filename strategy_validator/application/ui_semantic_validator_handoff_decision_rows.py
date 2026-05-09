"""Decision row synthesis and filtering for semantic validator handoff read-plane."""
from __future__ import annotations

from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_decision_common import (
    _BLOCKED_EVIDENCE_STATUS,
    _BLOCKED_LINEAGE_STATUS,
    _BLOCKED_REMEDIATION_STATUS,
    _BLOCKED_UNTRUSTED_STATUS,
    _DECISION_PRECONDITIONS,
    _READY_STATUS,
    _as_list,
    _contains,
    _digest,
    _s,
)


def _decision_status(review: dict[str, Any]) -> str:
    review_status = _s(review.get("review_status"))
    trust = _s(review.get("trust_banner"))
    if (
        bool(review.get("operator_review_allowed"))
        and review_status == "READY_FOR_OPERATOR_REVIEW"
        and trust == "TRUSTED"
        and int(review.get("review_block_count") or 0) == 0
        and int(review.get("remediation_step_count") or 0) == 0
    ):
        return _READY_STATUS
    if review_status == "EVIDENCE_REPAIR_REQUIRED":
        return _BLOCKED_EVIDENCE_STATUS
    if review_status == "LINEAGE_RECONSTRUCTION_REQUIRED":
        return _BLOCKED_LINEAGE_STATUS
    if trust == "UNTRUSTED":
        return _BLOCKED_UNTRUSTED_STATUS
    return _BLOCKED_REMEDIATION_STATUS


def _preconditions(review: dict[str, Any], decision_status: str) -> list[dict[str, Any]]:
    flags = {
        "review_gate_ready": _s(review.get("review_status")) == "READY_FOR_OPERATOR_REVIEW" and bool(review.get("operator_review_allowed")),
        "trust_banner_trusted": _s(review.get("trust_banner")) == "TRUSTED",
        "review_checklist_passed": int(review.get("review_pass_count") or 0) == int(review.get("review_check_count") or 0)
        and int(review.get("review_block_count") or 0) == 0,
        "no_remediation_steps": int(review.get("remediation_step_count") or 0) == 0,
        "authority_boundary_intact": not bool(review.get("validator_submission_allowed"))
        and not bool(review.get("promotion_allowed"))
        and not bool(review.get("execution_allowed")),
    }
    blocker_refs = {
        "review_gate_ready": [_s(review.get("review_status"))] if not flags["review_gate_ready"] else [],
        "trust_banner_trusted": [_s(review.get("trust_banner"))] if not flags["trust_banner_trusted"] else [],
        "review_checklist_passed": _as_list(review.get("review_blocker_codes")),
        "no_remediation_steps": [
            step.get("issue_code")
            for step in (review.get("remediation_steps") or [])
            if isinstance(step, dict) and step.get("issue_code")
        ],
        "authority_boundary_intact": [],
    }
    rows: list[dict[str, Any]] = []
    for spec in _DECISION_PRECONDITIONS:
        precondition_id = spec["precondition_id"]
        ok = bool(flags[precondition_id])
        refs = [str(ref) for ref in blocker_refs.get(precondition_id, []) if str(ref).strip()]
        rows.append(
            {
                "precondition_id": precondition_id,
                "label": spec["label"],
                "requirement": spec["requirement"],
                "status": "PASS" if ok else "BLOCK",
                "issue_refs": refs,
                "source_review_id": review.get("review_id"),
                "detail": "pass" if ok else (", ".join(refs) if refs else f"blocked by {decision_status}"),
            }
        )
    return rows


def _decision_options(decision_status: str, review: dict[str, Any]) -> list[dict[str, Any]]:
    ready = decision_status == _READY_STATUS
    return [
        {
            "option_id": "PREPARE_MANUAL_OPERATOR_SIGNOFF_DRAFT",
            "availability": "AVAILABLE" if ready else "BLOCKED",
            "requires_human_operator": True,
            "requires_external_mutation_workflow": True,
            "mutation_authority": "none_read_plane_external_operator_workflow_required",
            "rationale": "Ready chains may be summarized for a human signoff draft; this surface does not write that signoff.",
        },
        {
            "option_id": "RETURN_TO_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION",
            "availability": "AVAILABLE" if not ready else "OPTIONAL",
            "requires_human_operator": True,
            "requires_external_mutation_workflow": False,
            "mutation_authority": "none_read_plane_guidance_only",
            "rationale": "Blocked dossiers should be repaired or regenerated through the operator workflow indicated by remediation steps.",
        },
        {
            "option_id": "SUBMIT_TO_VALIDATOR_FROM_THIS_SURFACE",
            "availability": "FORBIDDEN",
            "requires_human_operator": True,
            "requires_external_mutation_workflow": True,
            "mutation_authority": "forbidden_read_plane_boundary",
            "rationale": "Decision dossiers are read-plane evidence summaries, not validator submission commands.",
        },
        {
            "option_id": "PROMOTE_OR_EXECUTE_FROM_THIS_SURFACE",
            "availability": "FORBIDDEN",
            "requires_human_operator": True,
            "requires_external_mutation_workflow": True,
            "mutation_authority": "forbidden_read_plane_boundary",
            "rationale": "Promotion and execution require separate governed authority paths and are never granted here.",
        },
    ]


def _decision_packet(review: dict[str, Any], decision_status: str, preconditions: list[dict[str, Any]]) -> dict[str, Any]:
    precondition_digest = _digest(
        [
            {
                "precondition_id": item.get("precondition_id"),
                "status": item.get("status"),
                "issue_refs": item.get("issue_refs"),
            }
            for item in preconditions
        ]
    )
    source_evidence = {
        "review_id": review.get("review_id"),
        "chain_id": review.get("chain_id"),
        "chain_digest": review.get("chain_digest"),
        "remediation_id": review.get("remediation_id"),
        "experiment_id": review.get("experiment_id"),
        "trust_banner": review.get("trust_banner"),
        "review_status": review.get("review_status"),
    }
    packet_digest = _digest([decision_status, precondition_digest, source_evidence, "validator_submission=false", "promotion=false", "execution=false"])
    return {
        "packet_schema_version": "semantic_validator_handoff_decision_packet/v1",
        "packet_digest": packet_digest,
        "precondition_digest": precondition_digest,
        "recommended_decision": "PREPARE_MANUAL_OPERATOR_SIGNOFF_DRAFT" if decision_status == _READY_STATUS else "DO_NOT_SIGN_OFF_REPAIR_REQUIRED",
        "human_reviewer_id": "<REQUIRED_EXTERNALLY>",
        "human_signoff_statement": "<REQUIRED_EXTERNALLY>",
        "source_evidence": source_evidence,
        "authority_assertions": {
            "read_plane_only": True,
            "validator_submission_allowed": False,
            "promotion_allowed": False,
            "execution_allowed": False,
            "artifact_mutation_allowed": False,
        },
    }


def _decision_row(review: dict[str, Any]) -> dict[str, Any]:
    decision_status = _decision_status(review)
    preconditions = _preconditions(review, decision_status)
    packet = _decision_packet(review, decision_status, preconditions)
    ready = decision_status == _READY_STATUS
    decision_id = "semantic-validator-decision-" + _digest(
        [review.get("review_id"), review.get("chain_digest"), decision_status, packet.get("packet_digest")]
    )[:20]
    return {
        "decision_id": decision_id,
        "decision_status": decision_status,
        "decision_ready": ready,
        "manual_operator_signoff_required": True,
        "manual_operator_signoff_preparable": ready,
        "manual_operator_signoff_recorded": False,
        "validator_submission_allowed": False,
        "validator_submission_gate": "NOT_AUTHORIZED_BY_READ_PLANE",
        "promotion_allowed": False,
        "execution_allowed": False,
        "artifact_mutation_allowed": False,
        "trust_banner": review.get("trust_banner"),
        "review_id": review.get("review_id"),
        "remediation_id": review.get("remediation_id"),
        "chain_id": review.get("chain_id"),
        "chain_digest": review.get("chain_digest"),
        "experiment_id": review.get("experiment_id"),
        "review_status": review.get("review_status"),
        "review_check_count": review.get("review_check_count", 0),
        "review_pass_count": review.get("review_pass_count", 0),
        "review_block_count": review.get("review_block_count", 0),
        "precondition_count": len(preconditions),
        "precondition_pass_count": sum(1 for item in preconditions if item.get("status") == "PASS"),
        "precondition_block_count": sum(1 for item in preconditions if item.get("status") != "PASS"),
        "decision_blocker_codes": sorted(
            dict.fromkeys(_as_list(review.get("review_blocker_codes")) + [item for pre in preconditions for item in _as_list(pre.get("issue_refs"))])
        ),
        "decision_preconditions": preconditions,
        "decision_options": _decision_options(decision_status, review),
        "decision_packet": packet,
        "source_review": review,
        "recommended_action": "PREPARE_MANUAL_OPERATOR_SIGNOFF_DRAFT" if ready else "RETURN_TO_REMEDIATION_BEFORE_DECISION",
        "summary_line": f"{review.get('experiment_id')} · {decision_status} · preconditions={sum(1 for item in preconditions if item.get('status') == 'PASS')}/{len(preconditions)} · submit=false",
    }


def _haystack(row: dict[str, Any]) -> str:
    parts = [
        _s(row.get("decision_status")),
        _s(row.get("trust_banner")),
        _s(row.get("review_status")),
        _s(row.get("recommended_action")),
        _s(row.get("summary_line")),
    ]
    parts.extend(_as_list(row.get("decision_blocker_codes")))
    for item in row.get("decision_preconditions") or []:
        parts.append(_s(item.get("precondition_id")))
        parts.append(_s(item.get("detail")))
        parts.extend(_as_list(item.get("issue_refs")))
    return "\n".join(parts)


def _matches(
    row: dict[str, Any],
    *,
    experiment_id_contains: str | None,
    issue_contains: str | None,
    decision_status: set[str],
    trust_banner: set[str],
    decision_ready: bool | None,
) -> bool:
    if not _contains(row.get("experiment_id"), experiment_id_contains):
        return False
    if issue_contains and not _contains(_haystack(row), issue_contains):
        return False
    if decision_status and _s(row.get("decision_status")).upper() not in decision_status:
        return False
    if trust_banner and _s(row.get("trust_banner")).upper() not in trust_banner:
        return False
    if decision_ready is not None and bool(row.get("decision_ready")) is not decision_ready:
        return False
    return True
