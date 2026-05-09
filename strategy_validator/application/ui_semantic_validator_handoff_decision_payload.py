"""Public payload builders for semantic validator handoff decision read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_decision_common import (
    _BLOCKED_EVIDENCE_STATUS,
    _LIMIT_MAX,
    _READY_STATUS,
    _SCHEMA_VERSION,
    _authority,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_decision_rows import _decision_row, _matches

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_decision as facade

    return facade.build_ui_semantic_validator_handoff_review_payload


def build_ui_semantic_validator_handoff_decision_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    decision_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    decision_ready: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    review_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    decision_rows = [_decision_row(row) for row in list(review_payload.get("reviews") or [])]
    status_filter = _norm_set(decision_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in decision_rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            decision_status=status_filter,
            trust_banner=trust_filter,
            decision_ready=decision_ready,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None

    degraded: list[str] = []
    if review_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_REVIEW_DEGRADED")
    if not decision_rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_DECISION_DOSSIERS_FOUND")
    if any(not bool(row.get("decision_ready")) for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_DECISION_BLOCKED_PRESENT")
    if any(row.get("trust_banner") == "UNTRUSTED" for row in filtered):
        degraded.append("UNTRUSTED_SEMANTIC_VALIDATOR_HANDOFF_DECISION_PRESENT")

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "source_schema_version": review_payload.get("schema_version"),
        "search_root": review_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "decision_status": list(status_filter),
            "trust_banner": list(trust_filter),
            "decision_ready": decision_ready,
            "limit": capped_limit,
        },
        "summary": {
            "decision_count_total": len(decision_rows),
            "decision_count_filtered": len(filtered),
            "decision_count_returned": len(returned),
            "ready_decision_count": sum(1 for row in filtered if row.get("decision_ready")),
            "blocked_decision_count": sum(1 for row in filtered if not bool(row.get("decision_ready"))),
            "manual_signoff_preparable_count": sum(1 for row in filtered if row.get("manual_operator_signoff_preparable")),
            "manual_signoff_recorded_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "trusted_count": sum(1 for row in filtered if row.get("trust_banner") == "TRUSTED"),
            "untrusted_count": sum(1 for row in filtered if row.get("trust_banner") == "UNTRUSTED"),
            "source_review_count_total": (review_payload.get("summary") or {}).get("review_count_total", 0),
            "source_ready_for_operator_review_count": (review_payload.get("summary") or {}).get("ready_for_operator_review_count", 0),
            "latest_decision_id": None if latest is None else latest.get("decision_id"),
            "latest_review_id": None if latest is None else latest.get("review_id"),
            "latest_chain_id": None if latest is None else latest.get("chain_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "decision_status_counts": _counts(filtered, "decision_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(review_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_signoff_write_or_artifact_mutation",
            "decision_dossier_is_not_operator_approval",
            "manual_signoff_fields_remain_external_placeholders",
            "validator_submission_promotion_and_execution_are_always_false",
            "decision_ready_requires_trusted_review_gate_and_zero_remediation_steps",
        ],
        "latest": latest,
        "decisions": returned,
    }


def build_ui_semantic_validator_handoff_decision_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_decision_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_decision_payload",
    "build_ui_semantic_validator_handoff_decision_latest_payload",
]
