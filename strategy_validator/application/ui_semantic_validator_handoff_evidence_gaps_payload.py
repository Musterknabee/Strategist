"""Public payload builders for semantic validator handoff evidence-gap visibility."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_common import (
    _LIMIT_MAX,
    _PRIORITY_RANK,
    _SCHEMA_VERSION,
    _STAGE_RANK,
    _as_list,
    _counts,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_evidence_gaps_rows import _gap_row, _matches

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_evidence_gaps as facade

    return facade.build_ui_semantic_validator_handoff_timeline_payload


def build_ui_semantic_validator_handoff_evidence_gaps_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    gap_kind: tuple[str, ...] = (),
    gap_state: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    stage: tuple[str, ...] = (),
    include_resolved: bool = False,
    limit: int = 200,
) -> dict[str, Any]:
    timeline_payload = _source_builder()(repo_root=repo_root, search_root=search_root, include_ready=True, limit=_LIMIT_MAX)
    events = [row for row in timeline_payload.get("timeline_events") or [] if isinstance(row, dict)]
    rows = [_gap_row(event, i) for i, event in enumerate(events)]
    filters = {
        "gap_kind": _norm_set(gap_kind),
        "gap_state": _norm_set(gap_state),
        "priority": _norm_set(priority),
        "severity": _norm_set(severity),
        "stage": _norm_set(stage),
    }
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            include_resolved=include_resolved,
            **filters,
        )
    ]
    filtered.sort(
        key=lambda row: (
            _PRIORITY_RANK.get(_s(row.get("priority")), 9),
            _s(row.get("experiment_id")),
            _STAGE_RANK.get(_s(row.get("stage")), 99),
            _s(row.get("gap_id")),
        )
    )
    capped = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped]
    latest = returned[0] if returned else None
    source_degraded = _as_list(timeline_payload.get("degraded"))
    degraded: list[str] = []
    if source_degraded:
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_DEGRADED")
    if any(row.get("gap_state") == "BLOCKED" for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_EVIDENCE_GAP_PRESENT")
    if any(row.get("gap_kind") == "MISSING_STAGE_EVIDENCE_GAP" for row in filtered):
        degraded.append("MISSING_SEMANTIC_VALIDATOR_HANDOFF_EVIDENCE_GAP_PRESENT")
    if any(row.get("gap_kind") == "EXTERNAL_ARTIFACT_GAP" for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_EXTERNAL_ARTIFACT_GAP_PRESENT")
    if not events:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_TIMELINE_EVENTS_FOUND")
    timeline_summary = timeline_payload.get("summary") if isinstance(timeline_payload.get("summary"), dict) else {}
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
        "source_schema_version": timeline_payload.get("schema_version"),
        "search_root": timeline_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "gap_kind": list(filters["gap_kind"]),
            "gap_state": list(filters["gap_state"]),
            "priority": list(filters["priority"]),
            "severity": list(filters["severity"]),
            "stage": list(filters["stage"]),
            "include_resolved": include_resolved,
            "limit": capped,
        },
        "summary": {
            "gap_count_total": len(rows),
            "gap_count_filtered": len(filtered),
            "gap_count_returned": len(returned),
            "open_gap_count": sum(1 for row in filtered if not row.get("resolved")),
            "blocked_gap_count": sum(1 for row in filtered if row.get("gap_state") == "BLOCKED"),
            "external_artifact_gap_count": sum(1 for row in filtered if row.get("gap_kind") == "EXTERNAL_ARTIFACT_GAP"),
            "missing_evidence_gap_count": sum(1 for row in filtered if row.get("gap_kind") == "MISSING_STAGE_EVIDENCE_GAP"),
            "attention_gap_count": sum(1 for row in filtered if row.get("gap_state") == "ATTENTION_REQUIRED"),
            "resolved_gap_excluded_count": sum(1 for row in rows if row.get("resolved")) if not include_resolved else 0,
            "source_timeline_event_count_total": timeline_summary.get("timeline_event_count_total"),
            "execution_allowed_count": 0,
            "promotion_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "mutation_allowed_count": 0,
            "latest_gap_id": None if latest is None else latest.get("gap_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
            "latest_gap_kind": None if latest is None else latest.get("gap_kind"),
            "latest_gap_state": None if latest is None else latest.get("gap_state"),
        },
        "gap_kind_counts": _counts(filtered, "gap_kind"),
        "gap_state_counts": _counts(filtered, "gap_state"),
        "priority_counts": _counts(filtered, "priority"),
        "stage_counts": _counts(filtered, "stage"),
        "severity_counts": _counts(filtered, "severity"),
        "source_degraded": source_degraded,
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_evidence_gap_cockpit_no_writes",
            "gap_rows_are_derived_visibility_not_repair_authority",
            "external_artifacts_must_be_created_outside_this_projection",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
        ],
        "latest": latest,
        "gap_rows": returned,
    }


def build_ui_semantic_validator_handoff_evidence_gaps_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_evidence_gaps_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_evidence_gaps_payload",
    "build_ui_semantic_validator_handoff_evidence_gaps_latest_payload",
]
