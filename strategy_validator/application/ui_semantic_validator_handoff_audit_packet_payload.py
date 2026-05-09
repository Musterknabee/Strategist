"""Public semantic validator handoff audit-packet payload builders."""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_common import (
    _DETAIL_ROUTES,
    _LIMIT_MAX,
    _SCHEMA_VERSION,
    _counts,
    _norm_set,
    _s,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_indexing import _index_rows, _related
from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_rows import _audit_packet_row, _matches

SourceBuilder = Callable[..., dict[str, Any]]


def _source_builders() -> tuple[SourceBuilder, SourceBuilder, SourceBuilder, SourceBuilder]:
    # Resolve through the legacy facade at call time so existing tests and
    # operators can monkeypatch the facade builder names without reaching into
    # subphase modules.
    from strategy_validator.application import ui_semantic_validator_handoff_audit_packet as facade

    return (
        facade.build_ui_semantic_validator_handoff_continuity_payload,
        facade.build_ui_semantic_validator_handoff_evidence_gaps_payload,
        facade.build_ui_semantic_validator_handoff_exceptions_payload,
        facade.build_ui_semantic_validator_handoff_timeline_payload,
    )


def build_ui_semantic_validator_handoff_audit_packet_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    packet_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    audit_ready: bool | None = None,
    operator_attention_required: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    continuity_builder, gaps_builder, exceptions_builder, timeline_builder = _source_builders()
    continuity_payload = continuity_builder(repo_root=repo_root, search_root=search_root, limit=_LIMIT_MAX)
    gaps_payload = gaps_builder(repo_root=repo_root, search_root=search_root, include_resolved=False, limit=_LIMIT_MAX)
    exceptions_payload = exceptions_builder(repo_root=repo_root, search_root=search_root, include_resolved=False, limit=_LIMIT_MAX)
    timeline_payload = timeline_builder(repo_root=repo_root, search_root=search_root, include_ready=True, limit=_LIMIT_MAX)

    continuities = [row for row in continuity_payload.get("continuity_rows") or [] if isinstance(row, dict)]
    gap_index = _index_rows(gaps_payload.get("gap_rows") or [])
    exception_index = _index_rows(exceptions_payload.get("exception_rows") or [])
    timeline_index = _index_rows(timeline_payload.get("timeline_events") or [])

    rows = [
        _audit_packet_row(
            continuity,
            gaps=_related(gap_index, continuity),
            exceptions=_related(exception_index, continuity),
            timeline_events=_related(timeline_index, continuity),
        )
        for continuity in continuities
    ]
    status_filter = _norm_set(packet_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            packet_status=status_filter,
            trust_banner=trust_filter,
            audit_ready=audit_ready,
            operator_attention_required=operator_attention_required,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), _LIMIT_MAX))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None

    degraded: list[str] = []
    if continuity_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CONTINUITY_DEGRADED")
    if gaps_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_EVIDENCE_GAPS_DEGRADED")
    if exceptions_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_EXCEPTIONS_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_AUDIT_PACKETS_FOUND")
    if any(row.get("operator_attention_required") for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_AUDIT_PACKET_ATTENTION_REQUIRED")
    if any(row.get("trust_banner") == "UNTRUSTED" for row in filtered):
        degraded.append("UNTRUSTED_SEMANTIC_VALIDATOR_HANDOFF_AUDIT_PACKET_PRESENT")

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "packet_materialization_authority": "none_read_plane",
        "external_artifact_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_versions": {
            "continuity": continuity_payload.get("schema_version"),
            "timeline": timeline_payload.get("schema_version"),
            "exceptions": exceptions_payload.get("schema_version"),
            "evidence_gaps": gaps_payload.get("schema_version"),
        },
        "search_root": continuity_payload.get("search_root")
        or gaps_payload.get("search_root")
        or exceptions_payload.get("search_root")
        or timeline_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "packet_status": list(status_filter),
            "trust_banner": list(trust_filter),
            "audit_ready": audit_ready,
            "operator_attention_required": operator_attention_required,
            "limit": capped_limit,
        },
        "summary": {
            "audit_packet_count_total": len(rows),
            "audit_packet_count_filtered": len(filtered),
            "audit_packet_count_returned": len(returned),
            "audit_ready_count": sum(1 for row in filtered if row.get("audit_ready")),
            "operator_attention_required_count": sum(1 for row in filtered if row.get("operator_attention_required")),
            "external_artifact_required_count": sum(1 for row in filtered if row.get("external_artifact_required")),
            "blocked_packet_count": sum(1 for row in filtered if _s(row.get("packet_lane")) == "blocked"),
            "trusted_count": sum(1 for row in filtered if row.get("trust_banner") == "TRUSTED"),
            "trust_restricted_count": sum(1 for row in filtered if row.get("trust_banner") == "TRUST_RESTRICTED"),
            "untrusted_count": sum(1 for row in filtered if row.get("trust_banner") == "UNTRUSTED"),
            "gap_count_total": sum(int(row.get("gap_count") or 0) for row in filtered),
            "exception_count_total": sum(int(row.get("exception_count") or 0) for row in filtered),
            "required_action_count_total": sum(int(row.get("required_action_count") or 0) for row in filtered),
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "latest_audit_packet_id": None if latest is None else latest.get("audit_packet_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
            "latest_packet_status": None if latest is None else latest.get("packet_status"),
        },
        "packet_status_counts": _counts(filtered, "packet_status"),
        "packet_lane_counts": _counts(filtered, "packet_lane"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "terminal_status_counts": _counts(filtered, "terminal_status"),
        "current_stage_counts": _counts(filtered, "current_stage"),
        "degraded": degraded,
        "source_degraded": {
            "continuity": list(continuity_payload.get("degraded") or []),
            "timeline": list(timeline_payload.get("degraded") or []),
            "exceptions": list(exceptions_payload.get("degraded") or []),
            "evidence_gaps": list(gaps_payload.get("degraded") or []),
        },
        "guardrails": [
            "read_plane_only_no_audit_packet_file_materialization",
            "consolidated_packet_is_visibility_not_operator_approval",
            "no_artifact_write_or_mutation_authority",
            "no_validator_submission_adjudication_promotion_or_execution_authority",
            "packet_digest_binds_read_plane_ids_and_digests_only",
        ],
        "routes": dict(_DETAIL_ROUTES),
        "latest": latest,
        "audit_packets": returned,
    }


def build_ui_semantic_validator_handoff_audit_packet_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_audit_packet_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_audit_packet_payload",
    "build_ui_semantic_validator_handoff_audit_packet_latest_payload",
]
