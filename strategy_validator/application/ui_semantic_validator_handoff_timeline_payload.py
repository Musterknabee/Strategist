"""Public payload builders for semantic validator handoff timeline visibility."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_timeline_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_timeline_rows import _matches, _timeline_events

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_timeline as facade

    return facade.build_ui_semantic_validator_handoff_continuity_payload


def build_ui_semantic_validator_handoff_timeline_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    stage: tuple[str, ...] = (),
    event_state: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    include_ready: bool = True,
    limit: int = 200,
) -> dict[str, Any]:
    continuity_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    events: list[dict[str, Any]] = []
    for row in continuity_payload.get("continuity_rows") or []:
        if isinstance(row, dict):
            events.extend(_timeline_events(row))
    stage_filter = _norm_set(stage)
    state_filter = _norm_set(event_state)
    severity_filter = _norm_set(severity)
    filtered = [
        row
        for row in events
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            stage=stage_filter,
            event_state=state_filter,
            severity=severity_filter,
            include_ready=include_ready,
        )
    ]
    filtered.sort(key=lambda row: (_s(row.get("experiment_id")), int(row.get("stage_position") or 0), _s(row.get("timeline_event_id"))))
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    source_degraded = _as_list(continuity_payload.get("degraded"))
    degraded: list[str] = []
    if source_degraded:
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CONTINUITY_DEGRADED")
    if any(row.get("event_state") == "BLOCKED" for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_EVENT_PRESENT")
    if any(row.get("event_state") == "MISSING_EVIDENCE" for row in filtered):
        degraded.append("MISSING_SEMANTIC_VALIDATOR_HANDOFF_STAGE_EVIDENCE_PRESENT")
    if any(row.get("external_artifact_required") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_EXTERNAL_ARTIFACT_REQUIRED")
    if not events:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_EVENTS_FOUND")
    summary_obj = continuity_payload.get("summary") if isinstance(continuity_payload.get("summary"), dict) else {}
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
        "source_schema_version": continuity_payload.get("schema_version"),
        "search_root": continuity_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "stage": list(stage_filter),
            "event_state": list(state_filter),
            "severity": list(severity_filter),
            "include_ready": include_ready,
            "limit": capped_limit,
        },
        "summary": {
            "timeline_event_count_total": len(events),
            "timeline_event_count_filtered": len(filtered),
            "timeline_event_count_returned": len(returned),
            "ready_event_count": sum(1 for row in filtered if row.get("event_state") == "RECORDED_READY"),
            "current_open_event_count": sum(1 for row in filtered if row.get("event_state") == "CURRENT_OPEN_STAGE"),
            "attention_event_count": sum(1 for row in filtered if row.get("event_state") == "ATTENTION_REQUIRED"),
            "blocked_event_count": sum(1 for row in filtered if row.get("event_state") == "BLOCKED"),
            "missing_evidence_event_count": sum(1 for row in filtered if row.get("event_state") == "MISSING_EVIDENCE"),
            "external_artifact_required_count": sum(1 for row in filtered if row.get("external_artifact_required")),
            "source_continuity_count_total": summary_obj.get("continuity_count_total"),
            "execution_allowed_count": 0,
            "promotion_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "mutation_allowed_count": 0,
            "latest_timeline_event_id": None if latest is None else latest.get("timeline_event_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
            "latest_stage": None if latest is None else latest.get("stage"),
            "latest_event_state": None if latest is None else latest.get("event_state"),
        },
        "event_state_counts": _counts(filtered, "event_state"),
        "stage_counts": _counts(filtered, "stage"),
        "severity_counts": _counts(filtered, "severity"),
        "terminal_status_counts": _counts(filtered, "terminal_status"),
        "source_degraded": source_degraded,
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_timeline_cockpit_no_writes",
            "timeline_events_are_derived_visibility_not_release_authority",
            "missing_stage_evidence_requires_external_repair_outside_this_projection",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
        ],
        "latest": latest,
        "timeline_events": returned,
    }


def build_ui_semantic_validator_handoff_timeline_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_timeline_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_timeline_payload",
    "build_ui_semantic_validator_handoff_timeline_latest_payload",
]
