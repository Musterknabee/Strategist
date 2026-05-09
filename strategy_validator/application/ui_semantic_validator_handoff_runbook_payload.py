"""Public payload builders for semantic validator handoff runbook read-plane."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_runbook_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _counts,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_runbook_rows import _matches, _runbook_card

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the compatibility facade at call time so legacy tests and
    # operator scripts can monkeypatch the historical source-builder symbol.
    from strategy_validator.application import ui_semantic_validator_handoff_runbook as facade

    return facade.build_ui_semantic_validator_handoff_continuity_payload


def build_ui_semantic_validator_handoff_runbook_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    action_kind: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    completed: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    continuity_payload = _source_builder()(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    cards = [_runbook_card(row) for row in continuity_payload.get("continuity_rows") or [] if isinstance(row, dict)]
    action_filter = _norm_set(action_kind)
    priority_filter = _norm_set(priority)
    severity_filter = _norm_set(severity)
    filtered = [
        card
        for card in cards
        if _matches(
            card,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            action_kind=action_filter,
            priority=priority_filter,
            severity=severity_filter,
            completed=completed,
        )
    ]
    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}
    filtered.sort(key=lambda card: (priority_rank.get(_s(card.get("priority")), 99), _s(card.get("experiment_id"))))
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if continuity_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CONTINUITY_DEGRADED")
    if not cards:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_RUNBOOK_CARDS_FOUND")
    if any(card.get("blocked") for card in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_RUNBOOK_ACTION_PRESENT")
    if any(card.get("external_artifact_required") for card in filtered):
        degraded.append("EXTERNAL_SEMANTIC_VALIDATOR_HANDOFF_ARTIFACT_REQUIRED")
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
            "action_kind": list(action_filter),
            "priority": list(priority_filter),
            "severity": list(severity_filter),
            "completed": completed,
            "limit": capped_limit,
        },
        "summary": {
            "runbook_card_count_total": len(cards),
            "runbook_card_count_filtered": len(filtered),
            "runbook_card_count_returned": len(returned),
            "open_runbook_card_count": sum(1 for card in filtered if not card.get("completed")),
            "completed_runbook_card_count": sum(1 for card in filtered if card.get("completed")),
            "blocked_runbook_card_count": sum(1 for card in filtered if card.get("blocked")),
            "external_artifact_required_count": sum(1 for card in filtered if card.get("external_artifact_required")),
            "execution_allowed_count": 0,
            "promotion_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "source_continuity_count_total": (continuity_payload.get("summary") or {}).get("continuity_count_total", 0),
            "source_open_action_count": (continuity_payload.get("summary") or {}).get("open_action_count", 0),
            "latest_runbook_card_id": None if latest is None else latest.get("runbook_card_id"),
            "latest_action_kind": None if latest is None else latest.get("action_kind"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "action_kind_counts": _counts(filtered, "action_kind"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "terminal_status_counts": _counts(filtered, "terminal_status"),
        "degraded": degraded,
        "source_degraded": list(continuity_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_operator_runbook_no_writes",
            "runbook_cards_are_guidance_not_artifact_creation",
            "external_attestations_and_manifests_must_be_created_outside_this_projection",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
            "completed_runbook_cards_are_audit_visibility_not_release_authority",
        ],
        "latest": latest,
        "runbook_cards": returned,
    }


def build_ui_semantic_validator_handoff_runbook_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_runbook_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_runbook_payload",
    "build_ui_semantic_validator_handoff_runbook_latest_payload",
]
