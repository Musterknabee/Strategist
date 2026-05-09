"""Public semantic validator handoff closure read-plane payload builders."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_archive import (
    build_ui_semantic_validator_handoff_archive_payload,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_attestations import (
    _closure_attestation_artifacts,
)
from strategy_validator.application.ui_semantic_validator_handoff_closure_common import (
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
from strategy_validator.application.ui_semantic_validator_handoff_closure_rows import (
    _closure_row,
    _matches,
)


def build_ui_semantic_validator_handoff_closure_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    experiment_id_contains: str | None = None,
    issue_contains: str | None = None,
    closure_status: tuple[str, ...] = (),
    trust_banner: tuple[str, ...] = (),
    closure_attestation_recorded: bool | None = None,
    limit: int = 200,
) -> dict[str, Any]:
    archive_payload = build_ui_semantic_validator_handoff_archive_payload(repo_root=repo_root, search_root=search_root, limit=1000)
    effective_search_root = search_root or archive_payload.get("search_root")
    closure_attestation_artifacts = _closure_attestation_artifacts(effective_search_root)
    rows = [_closure_row(archive, closure_attestation_artifacts) for archive in list(archive_payload.get("archive_gates") or [])]
    status_filter = _norm_set(closure_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [
        row
        for row in rows
        if _matches(
            row,
            experiment_id_contains=experiment_id_contains,
            issue_contains=issue_contains,
            closure_status=status_filter,
            trust_banner=trust_filter,
            closure_attestation_recorded=closure_attestation_recorded,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if archive_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_GATES_FOUND")
    if any(row.get("closure_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS} for row in filtered):
        degraded.append("INVALID_SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_ATTESTATION_PRESENT")
    if any(row.get("closure_status") == _BLOCKED_STATUS for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_PRESENT")
    if any(row.get("closure_status") == _READY_STATUS for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_CLOSURE_AWAITING_EXTERNAL_ATTESTATION")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "closure_write_authority": "none_read_plane",
        "archive_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": archive_payload.get("schema_version"),
        "search_root": archive_payload.get("search_root"),
        "filters": {
            "experiment_id_contains": experiment_id_contains,
            "issue_contains": issue_contains,
            "closure_status": list(status_filter),
            "trust_banner": list(trust_filter),
            "closure_attestation_recorded": closure_attestation_recorded,
            "limit": capped_limit,
        },
        "summary": {
            "closure_gate_count_total": len(rows),
            "closure_gate_count_filtered": len(filtered),
            "closure_gate_count_returned": len(returned),
            "external_closure_attestation_artifact_count": len(closure_attestation_artifacts),
            "recorded_closure_attestation_count": sum(1 for row in filtered if row.get("closure_status") == _RECORDED_STATUS),
            "ready_for_closure_attestation_count": sum(1 for row in filtered if row.get("closure_status") == _READY_STATUS),
            "invalid_closure_attestation_count": sum(1 for row in filtered if row.get("closure_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS}),
            "blocked_archive_count": sum(1 for row in filtered if row.get("closure_status") == _BLOCKED_STATUS),
            "closure_attestation_required_count": sum(1 for row in filtered if row.get("closure_attestation_required")),
            "closure_write_allowed_count": 0,
            "archive_write_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "source_archive_gate_count_total": (archive_payload.get("summary") or {}).get("archive_gate_count_total", 0),
            "source_verified_archive_manifest_count": (archive_payload.get("summary") or {}).get("verified_archive_manifest_count", 0),
            "latest_closure_gate_id": None if latest is None else latest.get("closure_gate_id"),
            "latest_closure_attestation_id": None if latest is None else latest.get("closure_attestation_id"),
            "latest_archive_gate_id": None if latest is None else latest.get("archive_gate_id"),
            "latest_archive_manifest_id": None if latest is None else latest.get("archive_manifest_id"),
            "latest_decision_id": None if latest is None else latest.get("decision_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "closure_status_counts": _counts(filtered, "closure_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(archive_payload.get("degraded") or []),
        "guardrails": [
            "read_plane_only_no_closure_write_or_artifact_mutation",
            "closure_attestations_must_be_created_by_external_human_workflow",
            "closure_matching_requires_packet_digest_continuity",
            "validator_submission_adjudication_promotion_and_execution_are_always_false",
            "recorded_closure_attestation_is_audit_evidence_only_not_release_promotion",
        ],
        "latest": latest,
        "closure_gates": returned,
        "external_closure_attestation_artifacts": closure_attestation_artifacts,
    }

def build_ui_semantic_validator_handoff_closure_latest_payload(
    *, repo_root: str | Path | None = None, search_root: str | Path | None = None
) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_closure_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = [
    "build_ui_semantic_validator_handoff_closure_payload",
    "build_ui_semantic_validator_handoff_closure_latest_payload",
]
