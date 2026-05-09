"""Public payload builders for semantic validator handoff read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_common import (
    _SCHEMA_VERSION,
    _as_list,
    _authority,
    _bool_counts,
    _coerce_root,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_discovery import _discover
from strategy_validator.application.ui_semantic_validator_handoff_rows import _matches


def build_ui_semantic_validator_handoff_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    artifact_kind: tuple[str, ...] = (),
    recommended_action: tuple[str, ...] = (),
    experiment_id_contains: str | None = None,
    certificate_id_contains: str | None = None,
    packet_id_contains: str | None = None,
    issue_contains: str | None = None,
    handoff_allowed: bool | None = None,
    verified: bool | None = None,
    ready_for_validator_ingress: bool | None = None,
    require_blockers: bool | None = None,
    limit: int = 200,
    include_raw: bool = False,
) -> dict[str, Any]:
    root = _coerce_root(repo_root=repo_root, search_root=search_root)
    entries, invalid = _discover(root, include_raw=include_raw)
    kind_filter = _norm_set(artifact_kind)
    action_filter = _norm_set(recommended_action)
    filtered = [
        entry
        for entry in entries
        if _matches(
            entry,
            artifact_kinds=kind_filter,
            recommended_actions=action_filter,
            experiment_id_contains=experiment_id_contains,
            certificate_id_contains=certificate_id_contains,
            packet_id_contains=packet_id_contains,
            issue_contains=issue_contains,
            handoff_allowed=handoff_allowed,
            verified=verified,
            ready_for_validator_ingress=ready_for_validator_ingress,
            require_blockers=require_blockers,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    verified_count = sum(1 for entry in filtered if bool(entry.get("verified")))
    handoff_allowed_count = sum(1 for entry in filtered if bool(entry.get("handoff_allowed")))
    ingress_ready_count = sum(1 for entry in filtered if bool(entry.get("ready_for_validator_ingress")))
    blocked_count = sum(1 for entry in filtered if len(_as_list(entry.get("blocker_codes"))) > 0)
    degraded: list[str] = []
    if invalid:
        degraded.append("INVALID_SEMANTIC_VALIDATOR_HANDOFF_ARTIFACTS_PRESENT")
    if not entries:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_ARTIFACTS_FOUND")
    if blocked_count:
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_BLOCKERS_PRESENT")
    if any(not bool(entry.get("verified")) for entry in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_SELF_VERIFICATION_FAILURES_PRESENT")
    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "search_root": str(root.as_posix()),
        "filters": {
            "artifact_kind": list(kind_filter),
            "recommended_action": list(action_filter),
            "experiment_id_contains": experiment_id_contains,
            "certificate_id_contains": certificate_id_contains,
            "packet_id_contains": packet_id_contains,
            "issue_contains": issue_contains,
            "handoff_allowed": handoff_allowed,
            "verified": verified,
            "ready_for_validator_ingress": ready_for_validator_ingress,
            "require_blockers": require_blockers,
            "limit": capped_limit,
            "include_raw": include_raw,
        },
        "summary": {
            "artifact_count_total": len(entries),
            "artifact_count_filtered": len(filtered),
            "artifact_count_returned": len(returned),
            "invalid_artifact_count": len(invalid),
            "decision_ledger_count": sum(1 for entry in filtered if entry.get("artifact_kind") == "decision_ledger"),
            "handoff_certificate_count": sum(1 for entry in filtered if entry.get("artifact_kind") == "handoff_certificate"),
            "validator_packet_count": sum(1 for entry in filtered if entry.get("artifact_kind") == "validator_packet"),
            "ingress_certificate_count": sum(1 for entry in filtered if entry.get("artifact_kind") == "ingress_certificate"),
            "verified_artifact_count": verified_count,
            "handoff_allowed_count": handoff_allowed_count,
            "validator_ingress_ready_count": ingress_ready_count,
            "blocked_artifact_count": blocked_count,
            "latest_artifact_id": None if latest is None else latest.get("artifact_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "artifact_kind_counts": _counts(filtered, "artifact_kind"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "verified_counts": _bool_counts(filtered, "verified"),
        "handoff_allowed_counts": _bool_counts(filtered, "handoff_allowed"),
        "validator_ingress_ready_counts": _bool_counts(filtered, "ready_for_validator_ingress"),
        "terminal_decision_counts": _counts(filtered, "terminal_decision"),
        "degraded": degraded,
        "invalid_artifacts": invalid,
        "guardrails": [
            "read_plane_only_no_artifact_creation_or_mutation",
            "no_validator_submission_or_adjudication_authority",
            "no_promotion_or_execution_authority",
            "self_verification_only_optional_source_replay_not_performed",
            "handoff_artifact_presence_is_not_operator_approval_or_live_readiness",
        ],
        "latest": latest,
        "artifacts": returned,
    }


def build_ui_semantic_validator_handoff_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = ["build_ui_semantic_validator_handoff_payload", "build_ui_semantic_validator_handoff_latest_payload"]
