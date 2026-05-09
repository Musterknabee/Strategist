"""Public semantic validator handoff action-queue payload builders."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_action_queue_common import (
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _as_list,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_action_queue_rows import _matches, _row, _sort_key

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builder() -> SourceBuilder:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder name without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_action_queue as facade

    return facade.build_ui_semantic_validator_handoff_audit_packet_payload


def build_ui_semantic_validator_handoff_action_queue_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    queue_state: tuple[str, ...] = (),
    priority: tuple[str, ...] = (),
    severity: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    source: tuple[str, ...] = (),
    external_artifact_required: bool | None = None,
    blocked: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    packet_payload = _source_builder()(
        repo_root=repo_root,
        search_root=search_root,
        experiment_id_contains=experiment_id_contains,
        issue_contains=issue_contains,
        limit=_LIMIT_MAX,
    )
    packets = [packet for packet in packet_payload.get("audit_packets", []) if isinstance(packet, dict)]
    rows = []
    for packet in packets:
        for index, action in enumerate(
            action for action in packet.get("required_actions", []) if isinstance(action, dict)
        ):
            rows.append(_row(packet, action, index))

    rows = sorted(rows, key=_sort_key)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            queue_state=_norm_set(queue_state),
            priority=_norm_set(priority),
            severity=_norm_set(severity),
            trust_banner=_norm_set(trust_banner),
            source=_norm_set(source),
            external_artifact_required=external_artifact_required,
            blocked=blocked,
        )
    ]
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None

    source_degraded = _as_list(packet_payload.get("degraded"))
    degraded = []
    if source_degraded:
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_AUDIT_PACKET_DEGRADED")
    if any(row.get("blocked") for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_ACTION_PRESENT")
    if any(row.get("external_artifact_required") for row in filtered):
        degraded.append("EXTERNAL_ARTIFACT_SEMANTIC_VALIDATOR_HANDOFF_ACTION_PRESENT")

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "action_execution_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": packet_payload.get("schema_version"),
        "search_root": packet_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "limit": capped_limit,
        },
        "summary": {
            "source_audit_packet_count": len(packets),
            "action_count_total": len(rows),
            "action_count_filtered": len(filtered),
            "action_count_returned": len(returned),
            "blocked_count": sum(1 for row in filtered if row.get("blocked")),
            "external_artifact_required_count": sum(
                1 for row in filtered if row.get("external_artifact_required")
            ),
            "operator_attention_required_count": sum(
                1 for row in filtered if row.get("operator_attention_required")
            ),
            "execution_allowed_count": 0,
            "latest_action_id": None if latest is None else latest.get("action_id"),
        },
        "queue_state_counts": _counts(filtered, "queue_state"),
        "priority_counts": _counts(filtered, "priority"),
        "severity_counts": _counts(filtered, "severity"),
        "source_counts": _counts(filtered, "source"),
        "route_counts": _counts(filtered, "route"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "packet_status_counts": _counts(filtered, "packet_status"),
        "source_degraded": source_degraded,
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_action_queue_no_repair_or_execution_is_performed_here",
            "external_artifacts_must_be_created_outside_this_projection",
            "no_validator_submission_adjudication_promotion_or_execution_authority",
        ],
        "routes": {
            "action_queue": "/ui/semantic-validator-handoff/action-queue",
            "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
            "closure": "/ui/semantic-validator-handoff/closure",
        },
        "latest": latest,
        "action_rows": returned,
    }


def build_ui_semantic_validator_handoff_action_queue_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_action_queue_payload(
        repo_root=repo_root, search_root=search_root, limit=1
    )


__all__ = [
    "build_ui_semantic_validator_handoff_action_queue_payload",
    "build_ui_semantic_validator_handoff_action_queue_latest_payload",
]
