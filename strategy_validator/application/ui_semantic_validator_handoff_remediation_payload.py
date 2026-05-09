"""Public payload builders for semantic validator handoff remediation read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_remediation_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _authority,
    _counts,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_remediation_rows import (
    _build_remediation_record,
    _matches,
)

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so existing tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_remediation as facade

    return facade.build_ui_semantic_validator_handoff_lineage_payload


def build_ui_semantic_validator_handoff_remediation_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    chain_status: tuple[str, ...] = (),
    remediation_status: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    require_operator_action: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    lineage = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        limit=_LIMIT_MAX,
    )
    rows = [_build_remediation_record(chain) for chain in lineage.get("chains") or []]
    rows.sort(
        key=lambda row: (int(row.get("priority_score") or 0), _s(row.get("experiment_id")), _s(row.get("remediation_id"))),
        reverse=True,
    )
    chain_status_filter = _norm_set(chain_status)
    remediation_status_filter = _norm_set(remediation_status)
    severity_filter = _norm_set(severity)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            chain_status=chain_status_filter,
            remediation_status=remediation_status_filter,
            severity=severity_filter,
            require_operator_action=require_operator_action,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    degraded: list[str] = []
    if lineage.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_RECORDS_FOUND")
    if any(row.get("operator_action_required") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_ACTION_REQUIRED")
    if any(row.get("severity") == "CRITICAL" for row in filtered):
        degraded.append("CRITICAL_SEMANTIC_VALIDATOR_HANDOFF_REMEDIATION_PRESENT")
    latest = returned[0] if returned else None
    action_required = [row for row in filtered if row.get("operator_action_required")]
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        **_authority(),
        "source_schema_version": lineage.get("schema_version"),
        "search_root": lineage.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "chain_status": list(chain_status_filter),
            "remediation_status": list(remediation_status_filter),
            "severity": list(severity_filter),
            "require_operator_action": require_operator_action,
            "limit": capped_limit,
        },
        "summary": {
            "remediation_count_total": len(rows),
            "remediation_count_filtered": len(filtered),
            "remediation_count_returned": len(returned),
            "action_required_count": len(action_required),
            "ready_no_action_count": sum(1 for row in filtered if row.get("remediation_status") == "READY_NO_ACTION"),
            "critical_count": sum(1 for row in filtered if row.get("severity") == "CRITICAL"),
            "high_count": sum(1 for row in filtered if row.get("severity") == "HIGH"),
            "blocked_validator_ingress_count": sum(1 for row in filtered if bool(row.get("validator_ingress_blocked"))),
            "lineage_chain_count_total": (lineage.get("summary") or {}).get("chain_count_total", 0),
            "lineage_ready_chain_count": (lineage.get("summary") or {}).get("ready_chain_count", 0),
            "lineage_broken_chain_count": (lineage.get("summary") or {}).get("broken_chain_count", 0),
            "lineage_incomplete_chain_count": (lineage.get("summary") or {}).get("incomplete_chain_count", 0),
            "latest_remediation_id": None if latest is None else latest.get("remediation_id"),
            "latest_chain_id": None if latest is None else latest.get("chain_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "remediation_status_counts": _counts(filtered, "remediation_status"),
        "severity_counts": _counts(filtered, "severity"),
        "chain_status_counts": _counts(filtered, "chain_status"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(lineage.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_artifact_creation_or_mutation",
            "no_validator_submission_or_adjudication_authority",
            "remediation_steps_are_operator_guidance_not_approval",
            "do_not_edit_ids_or_checksums_manually_regenerate_from_upstream_artifacts",
            "lineage_remediation_readiness_is_not_live_execution_readiness",
        ],
        "latest": latest,
        "remediations": returned,
    }


def build_ui_semantic_validator_handoff_remediation_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_remediation_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_remediation_payload",
    "build_ui_semantic_validator_handoff_remediation_latest_payload",
]
