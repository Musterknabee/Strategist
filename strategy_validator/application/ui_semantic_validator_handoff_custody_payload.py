"""Public semantic validator-handoff custody payload builders."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_custody_common import (
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _RECORDED_STATUS,
    _SCHEMA_VERSION,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_rows import (
    _custody_row,
    _matches,
)
from strategy_validator.application.ui_semantic_validator_handoff_custody_seals import _custody_seal_artifacts
from strategy_validator.application.ui_semantic_validator_handoff_signoff import (
    build_ui_semantic_validator_handoff_signoff_payload,
)


def build_ui_semantic_validator_handoff_custody_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    custody_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    custody_seal_recorded: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    signoff_payload = build_ui_semantic_validator_handoff_signoff_payload(repo_root=repo_root, search_root=search_root, limit=1000)
    effective_search_root = search_root or signoff_payload.get("search_root")
    custody_seal_artifacts = _custody_seal_artifacts(effective_search_root)
    rows = [_custody_row(signoff, custody_seal_artifacts) for signoff in list(signoff_payload.get("signoffs") or [])]
    status_filter = _norm_set(custody_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            custody_status=status_filter,
            trust_banner=trust_filter,
            custody_seal_recorded=custody_seal_recorded,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if signoff_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_GATES_FOUND")
    if any(row.get("custody_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS} for row in filtered):
        degraded.append("INVALID_SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_SEAL_PRESENT")
    if any(row.get("custody_status") == _BLOCKED_STATUS for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_SIGNOFF_PRESENT")
    if any(row.get("custody_status") == _READY_STATUS for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_AWAITING_EXTERNAL_SEAL")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "custody_seal_write_authority": "none_read_plane",
        "archive_write_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": signoff_payload.get("schema_version"),
        "search_root": signoff_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "custody_status": list(status_filter),
            "trust_banner": list(trust_filter),
            "custody_seal_recorded": custody_seal_recorded,
            "limit": capped_limit,
        },
        "summary": {
            "custody_gate_count_total": len(rows),
            "custody_gate_count_filtered": len(filtered),
            "custody_gate_count_returned": len(returned),
            "external_custody_seal_artifact_count": len(custody_seal_artifacts),
            "recorded_custody_seal_count": sum(1 for row in filtered if row.get("custody_status") == _RECORDED_STATUS),
            "ready_for_custody_seal_count": sum(1 for row in filtered if row.get("custody_status") == _READY_STATUS),
            "invalid_custody_seal_count": sum(1 for row in filtered if row.get("custody_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS}),
            "blocked_signoff_count": sum(1 for row in filtered if row.get("custody_status") == _BLOCKED_STATUS),
            "custody_seal_required_count": sum(1 for row in filtered if row.get("custody_seal_required")),
            "custody_seal_write_allowed_count": 0,
            "archive_write_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "source_signoff_gate_count_total": (signoff_payload.get("summary") or {}).get("signoff_gate_count_total", 0),
            "source_recorded_signoff_count": (signoff_payload.get("summary") or {}).get("recorded_signoff_count", 0),
            "latest_custody_gate_id": None if latest is None else latest.get("custody_gate_id"),
            "latest_custody_seal_id": None if latest is None else latest.get("custody_seal_id"),
            "latest_signoff_gate_id": None if latest is None else latest.get("signoff_gate_id"),
            "latest_decision_id": None if latest is None else latest.get("decision_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "custody_status_counts": _counts(filtered, "custody_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(signoff_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_custody_seal_write_or_archive_write",
            "custody_seals_must_be_created_by_external_human_workflow",
            "custody_matching_requires_packet_digest_continuity",
            "validator_submission_promotion_and_execution_are_always_false",
            "recorded_custody_is_evidence_only_not_archive_creation",
        ],
        "latest": latest,
        "custody_gates": returned,
        "external_custody_seal_artifacts": custody_seal_artifacts,
    }


def build_ui_semantic_validator_handoff_custody_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_custody_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_custody_payload",
    "build_ui_semantic_validator_handoff_custody_latest_payload",
]
