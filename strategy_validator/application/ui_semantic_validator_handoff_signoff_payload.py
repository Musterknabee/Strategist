"""Public payload builders for semantic validator handoff signoff read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_signoff_artifacts import _signoff_artifacts
from strategy_validator.application.ui_semantic_validator_handoff_signoff_common import (
    _AWAITING_STATUS,
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _LIMIT_MAX,
    _RECORDED_STATUS,
    _SCHEMA_VERSION,
    _authority,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_signoff_rows import _matches, _signoff_row

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_signoff as facade

    return facade.build_ui_semantic_validator_handoff_decision_payload


def build_ui_semantic_validator_handoff_signoff_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    signoff_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    signoff_recorded: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    decision_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    effective_search_root = search_root or decision_payload.get("search_root")
    signoff_artifacts = _signoff_artifacts(effective_search_root)
    rows = [_signoff_row(decision, signoff_artifacts) for decision in list(decision_payload.get("decisions") or [])]
    status_filter = _norm_set(signoff_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            signoff_status=status_filter,
            trust_banner=trust_filter,
            signoff_recorded=signoff_recorded,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if decision_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_DECISION_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_GATES_FOUND")
    if any(row.get("signoff_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS} for row in filtered):
        degraded.append("INVALID_SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_PRESENT")
    if any(row.get("signoff_status") == _BLOCKED_STATUS for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_DECISION_PRESENT")
    if any(row.get("signoff_status") == _AWAITING_STATUS for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_AWAITING_OPERATOR")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "source_schema_version": decision_payload.get("schema_version"),
        "search_root": decision_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "signoff_status": list(status_filter),
            "trust_banner": list(trust_filter),
            "signoff_recorded": signoff_recorded,
            "limit": capped_limit,
        },
        "summary": {
            "signoff_gate_count_total": len(rows),
            "signoff_gate_count_filtered": len(filtered),
            "signoff_gate_count_returned": len(returned),
            "external_signoff_artifact_count": len(signoff_artifacts),
            "recorded_signoff_count": sum(1 for row in filtered if row.get("signoff_status") == _RECORDED_STATUS),
            "awaiting_signoff_count": sum(1 for row in filtered if row.get("signoff_status") == _AWAITING_STATUS),
            "invalid_signoff_count": sum(
                1 for row in filtered if row.get("signoff_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS}
            ),
            "blocked_decision_count": sum(1 for row in filtered if row.get("signoff_status") == _BLOCKED_STATUS),
            "signoff_required_count": sum(1 for row in filtered if row.get("signoff_required")),
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "source_decision_count_total": (decision_payload.get("summary") or {}).get("decision_count_total", 0),
            "source_ready_decision_count": (decision_payload.get("summary") or {}).get("ready_decision_count", 0),
            "latest_signoff_gate_id": None if latest is None else latest.get("signoff_gate_id"),
            "latest_signoff_id": None if latest is None else latest.get("signoff_id"),
            "latest_decision_id": None if latest is None else latest.get("decision_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "signoff_status_counts": _counts(filtered, "signoff_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(decision_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_signoff_write_or_artifact_mutation",
            "operator_signoff_receipts_must_be_created_by_external_human_workflow",
            "signoff_matching_requires_decision_packet_digest_continuity",
            "validator_submission_promotion_and_execution_are_always_false",
            "recorded_signoff_is_evidence_only_not_validator_submission",
        ],
        "latest": latest,
        "signoffs": returned,
        "external_signoff_artifacts": signoff_artifacts,
    }


def build_ui_semantic_validator_handoff_signoff_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_signoff_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_signoff_payload",
    "build_ui_semantic_validator_handoff_signoff_latest_payload",
]
