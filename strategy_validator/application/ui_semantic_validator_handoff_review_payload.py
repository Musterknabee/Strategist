"""Public payload builders for semantic validator handoff review read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_review_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _authority,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_review_rows import _matches, _review_row

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_review as facade

    return facade.build_ui_semantic_validator_handoff_remediation_payload


def build_ui_semantic_validator_handoff_review_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    review_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    operator_review_allowed: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    remediation = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    review_rows = [_review_row(row) for row in list(remediation.get("remediations") or [])]
    review_status_filter = _norm_set(review_status)
    trust_banner_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in review_rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            review_status=review_status_filter,
            operator_review_allowed=operator_review_allowed,
            trust_banner=trust_banner_filter,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None

    degraded: list[str] = []
    if remediation.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_DEGRADED")
    if not review_rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_REVIEW_RECORDS_FOUND")
    if any(not bool(row.get("operator_review_allowed")) for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_REVIEW_BLOCKED_PRESENT")
    if any(row.get("trust_banner") == "UNTRUSTED" for row in filtered):
        degraded.append("UNTRUSTED_SEMANTIC_VALIDATOR_HANDOFF_REVIEW_PRESENT")

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "source_schema_version": remediation.get("schema_version"),
        "search_root": remediation.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "review_status": list(review_status_filter),
            "trust_banner": list(trust_banner_filter),
            "operator_review_allowed": operator_review_allowed,
            "limit": capped_limit,
        },
        "summary": {
            "review_count_total": len(review_rows),
            "review_count_filtered": len(filtered),
            "review_count_returned": len(returned),
            "ready_for_operator_review_count": sum(1 for row in filtered if row.get("review_status") == "READY_FOR_OPERATOR_REVIEW"),
            "blocked_review_count": sum(1 for row in filtered if not bool(row.get("operator_review_allowed"))),
            "trusted_count": sum(1 for row in filtered if row.get("trust_banner") == "TRUSTED"),
            "trust_restricted_count": sum(1 for row in filtered if row.get("trust_banner") == "TRUST_RESTRICTED"),
            "untrusted_count": sum(1 for row in filtered if row.get("trust_banner") == "UNTRUSTED"),
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "source_remediation_count_total": (remediation.get("summary") or {}).get("remediation_count_total", 0),
            "source_action_required_count": (remediation.get("summary") or {}).get("action_required_count", 0),
            "latest_review_id": None if latest is None else latest.get("review_id"),
            "latest_chain_id": None if latest is None else latest.get("chain_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "review_status_counts": _counts(filtered, "review_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(remediation.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_artifact_creation_or_mutation",
            "operator_review_allowed_is_not_approval_or_validator_submission",
            "validator_submission_promotion_and_execution_are_always_false",
            "review_gate_requires_complete_lineage_clean_remediation_and_ingress_readiness",
            "trust_banner_is_derived_from_read_plane_evidence_only",
        ],
        "latest": latest,
        "reviews": returned,
    }


def build_ui_semantic_validator_handoff_review_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_review_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_review_payload",
    "build_ui_semantic_validator_handoff_review_latest_payload",
]
