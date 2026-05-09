"""Public payload builders for semantic validator handoff lineage read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_lineage_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _authority,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_lineage_rows import (
    _build_chains,
    _matches,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so existing tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_lineage as facade

    return facade.build_ui_semantic_validator_handoff_payload


def build_ui_semantic_validator_handoff_lineage_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    chain_status: tuple[str, ...] = (),
    ready_for_operator_review: bool | None = None,
    require_broken_links: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    base = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        limit=_LIMIT_MAX,
        include_raw=False,
    )
    chains = _build_chains(list(base.get("artifacts") or []))
    status_filter = _norm_set(chain_status)
    filtered = [
        row
        for row in chains
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            chain_status=status_filter,
            ready_for_operator_review=ready_for_operator_review,
            require_broken_links=require_broken_links,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    degraded: list[str] = []
    if base.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_PROJECTION_DEGRADED")
    if not chains:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_CHAINS_FOUND")
    if any(row.get("status") == "BROKEN" for row in filtered):
        degraded.append("BROKEN_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_PRESENT")
    if any(row.get("status") == "INCOMPLETE" for row in filtered):
        degraded.append("INCOMPLETE_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_PRESENT")
    if any(not bool(row.get("ready_for_operator_review")) for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_NOT_READY_FOR_OPERATOR_REVIEW")

    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "source_schema_version": base.get("schema_version"),
        "search_root": base.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "chain_status": list(status_filter),
            "ready_for_operator_review": ready_for_operator_review,
            "require_broken_links": require_broken_links,
            "limit": capped_limit,
        },
        "summary": {
            "chain_count_total": len(chains),
            "chain_count_filtered": len(filtered),
            "chain_count_returned": len(returned),
            "ready_chain_count": sum(1 for row in filtered if row.get("status") == "READY"),
            "broken_chain_count": sum(1 for row in filtered if row.get("status") == "BROKEN"),
            "incomplete_chain_count": sum(1 for row in filtered if row.get("status") == "INCOMPLETE"),
            "operator_review_ready_count": sum(1 for row in filtered if bool(row.get("ready_for_operator_review"))),
            "validator_ingress_ready_count": sum(1 for row in filtered if bool(row.get("ready_for_validator_ingress"))),
            "source_artifact_count_total": (base.get("summary") or {}).get("artifact_count_total", 0),
            "source_invalid_artifact_count": (base.get("summary") or {}).get("invalid_artifact_count", 0),
            "latest_chain_id": None if latest is None else latest.get("chain_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "chain_status_counts": _counts(filtered, "status"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(base.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_artifact_creation_or_mutation",
            "no_validator_submission_or_adjudication_authority",
            "no_promotion_or_execution_authority",
            "lineage_readiness_is_not_operator_approval_or_live_readiness",
            "link_integrity_checks_use_artifact_ids_and_payload_checksums_only",
        ],
        "latest": latest,
        "chains": returned,
    }


def build_ui_semantic_validator_handoff_lineage_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_lineage_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_lineage_payload",
    "build_ui_semantic_validator_handoff_lineage_latest_payload",
]
