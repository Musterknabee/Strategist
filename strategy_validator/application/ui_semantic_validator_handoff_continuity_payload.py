"""Public payload builders for semantic validator handoff continuity chains."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_continuity_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_continuity_rows import _continuity_row, _matches

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so historical tests
    # and operator scripts can monkeypatch the legacy source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_continuity as facade

    return facade.build_ui_semantic_validator_handoff_closure_payload


def build_ui_semantic_validator_handoff_continuity_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    terminal_status: tuple[str, ...] = (),
    current_stage: tuple[str, ...] = (),
    open_action: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    closure_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    rows = [_continuity_row(row) for row in closure_payload.get("closure_gates") or [] if isinstance(row, dict)]
    terminal_filter = _norm_set(terminal_status)
    stage_filter = _norm_set(current_stage)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            terminal_status=terminal_filter,
            current_stage=stage_filter,
            open_action=open_action,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if closure_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_CONTINUITY_ROWS_FOUND")
    if any(row.get("open_action") for row in filtered):
        degraded.append("OPEN_SEMANTIC_VALIDATOR_HANDOFF_CONTINUITY_ACTION_PRESENT")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": closure_payload.get("schema_version"),
        "search_root": closure_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "terminal_status": list(terminal_filter),
            "current_stage": list(stage_filter),
            "open_action": open_action,
            "limit": capped_limit,
        },
        "summary": {
            "continuity_count_total": len(rows),
            "continuity_count_filtered": len(filtered),
            "continuity_count_returned": len(returned),
            "open_action_count": sum(1 for row in filtered if row.get("open_action")),
            "closed_chain_count": sum(1 for row in filtered if row.get("terminal_status") == "CLOSED_WITH_RECORDED_CLOSURE_ATTESTATION"),
            "external_artifact_required_count": sum(1 for row in filtered if row.get("external_artifact_required")),
            "execution_allowed_count": 0,
            "promotion_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "latest_continuity_id": None if latest is None else latest.get("continuity_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
            "latest_terminal_status": None if latest is None else latest.get("terminal_status"),
        },
        "terminal_status_counts": _counts(filtered, "terminal_status"),
        "current_stage_counts": _counts(filtered, "current_stage"),
        "closure_status_counts": _counts(filtered, "closure_status"),
        "severity_counts": _counts(filtered, "severity"),
        "degraded": degraded,
        "source_degraded": list(closure_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_continuity_no_writes",
            "continuity_rows_are_audit_visibility_not_external_artifact_creation",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
            "closed_continuity_is_evidence_only_not_live_execution_authority",
        ],
        "latest": latest,
        "continuity_rows": returned,
    }


def build_ui_semantic_validator_handoff_continuity_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_continuity_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_continuity_payload",
    "build_ui_semantic_validator_handoff_continuity_latest_payload",
]
