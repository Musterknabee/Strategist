"""Public payload builders for semantic validator handoff exception queue."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_exceptions_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_exceptions_rows import _exception_row, _matches

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so historical tests
    # and operator scripts can monkeypatch the legacy source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_exceptions as facade

    return facade.build_ui_semantic_validator_handoff_runbook_payload


def build_ui_semantic_validator_handoff_exceptions_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    exception_state: tuple[str, ...] = (),
    exception_kind: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    include_resolved: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    runbook_payload = _source_builder()(repo_root=repo_root, search_root=search_root, completed=None, limit=_LIMIT_MAX)
    rows = [_exception_row(card) for card in runbook_payload.get("runbook_cards") or [] if isinstance(card, dict)]
    state_filter = _norm_set(exception_state)
    kind_filter = _norm_set(exception_kind)
    priority_filter = _norm_set(priority)
    severity_filter = _norm_set(severity)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            exception_state=state_filter,
            exception_kind=kind_filter,
            priority=priority_filter,
            severity=severity_filter,
            include_resolved=include_resolved,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if runbook_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_RUNBOOK_DEGRADED")
    if any(row.get("blocked") for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_EXCEPTION_PRESENT")
    if any(row.get("external_artifact_required") for row in filtered):
        degraded.append("EXTERNAL_SEMANTIC_VALIDATOR_HANDOFF_EXCEPTION_ARTIFACT_REQUIRED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_EXCEPTION_ROWS_FOUND")
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
        "source_schema_version": runbook_payload.get("schema_version"),
        "search_root": runbook_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "exception_state": list(state_filter),
            "exception_kind": list(kind_filter),
            "priority": list(priority_filter),
            "severity": list(severity_filter),
            "include_resolved": include_resolved,
            "limit": capped_limit,
        },
        "summary": {
            "exception_count_total": len(rows),
            "exception_count_filtered": len(filtered),
            "exception_count_returned": len(returned),
            "open_exception_count": sum(1 for row in filtered if not row.get("completed")),
            "blocked_exception_count": sum(1 for row in filtered if row.get("blocked")),
            "external_artifact_required_count": sum(1 for row in filtered if row.get("external_artifact_required")),
            "resolved_exception_count": sum(1 for row in rows if row.get("completed")),
            "resolved_exception_excluded_count": 0 if include_resolved else sum(1 for row in rows if row.get("completed")),
            "p0_exception_count": sum(1 for row in filtered if row.get("priority") == "P0"),
            "execution_allowed_count": 0,
            "promotion_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "source_runbook_card_count_total": (runbook_payload.get("summary") or {}).get("runbook_card_count_total"),
            "source_open_runbook_card_count": (runbook_payload.get("summary") or {}).get("open_runbook_card_count"),
            "latest_exception_id": None if latest is None else latest.get("exception_id"),
            "latest_exception_kind": None if latest is None else latest.get("exception_kind"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "exception_state_counts": _counts(filtered, "exception_state"),
        "exception_kind_counts": _counts(filtered, "exception_kind"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "escalation_lane_counts": _counts(filtered, "escalation_lane"),
        "degraded": degraded,
        "source_degraded": list(runbook_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_exception_queue_no_writes",
            "exception_rows_are_operator_visibility_not_artifact_creation",
            "external_artifact_requirements_must_be_fulfilled_outside_this_projection",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
        ],
        "latest": latest,
        "exception_rows": returned,
    }


def build_ui_semantic_validator_handoff_exceptions_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_exceptions_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_exceptions_payload",
    "build_ui_semantic_validator_handoff_exceptions_latest_payload",
]
