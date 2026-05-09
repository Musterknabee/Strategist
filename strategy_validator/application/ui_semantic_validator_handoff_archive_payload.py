"""Public semantic validator-handoff archive payload builders."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.ui_semantic_validator_handoff_archive_common import (
    _BLOCKED_STATUS,
    _DIGEST_MISMATCH_STATUS,
    _INVALID_STATUS,
    _READY_STATUS,
    _SCHEMA_VERSION,
    _VERIFIED_STATUS,
    _counts,
    _norm_set,
    _utc_now,
)
from strategy_validator.application.ui_semantic_validator_handoff_archive_manifests import _archive_manifest_artifacts
from strategy_validator.application.ui_semantic_validator_handoff_archive_rows import _archive_row, _matches
from strategy_validator.application.ui_semantic_validator_handoff_custody import build_ui_semantic_validator_handoff_custody_payload


def build_ui_semantic_validator_handoff_archive_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None, experiment_id_contains: str | None = None, issue_contains: str | None = None, archive_status: tuple[str, ...] = (), trust_banner: tuple[str, ...] = (), archive_manifest_verified: bool | None = None, limit: int = 200) -> dict[str, Any]:
    custody_payload = build_ui_semantic_validator_handoff_custody_payload(repo_root=repo_root, search_root=search_root, limit=1000)
    effective_search_root = search_root or custody_payload.get("search_root")
    archive_manifest_artifacts = _archive_manifest_artifacts(effective_search_root)
    rows = [_archive_row(custody, archive_manifest_artifacts) for custody in list(custody_payload.get("custody_gates") or [])]
    status_filter = _norm_set(archive_status)
    trust_filter = _norm_set(trust_banner)
    filtered = [row for row in rows if _matches(row, experiment_id_contains=experiment_id_contains, issue_contains=issue_contains, archive_status=status_filter, trust_banner=trust_filter, archive_manifest_verified=archive_manifest_verified)]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if custody_payload.get("degraded"):
        degraded.append("SOURCE_SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_DEGRADED")
    if not rows:
        degraded.append("NO_SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_GATES_FOUND")
    if any(row.get("archive_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS} for row in filtered):
        degraded.append("INVALID_SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_MANIFEST_PRESENT")
    if any(row.get("archive_status") == _BLOCKED_STATUS for row in filtered):
        degraded.append("BLOCKED_SEMANTIC_VALIDATOR_HANDOFF_CUSTODY_PRESENT")
    if any(row.get("archive_status") == _READY_STATUS for row in filtered):
        degraded.append("SEMANTIC_VALIDATOR_HANDOFF_ARCHIVE_AWAITING_EXTERNAL_MANIFEST")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "archive_write_authority": "none_read_plane",
        "artifact_mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "source_schema_version": custody_payload.get("schema_version"),
        "search_root": custody_payload.get("search_root"),
        "filters": {"experiment_id_contains": experiment_id_contains, "issue_contains": issue_contains, "archive_status": list(status_filter), "trust_banner": list(trust_filter), "archive_manifest_verified": archive_manifest_verified, "limit": capped_limit},
        "summary": {
            "archive_gate_count_total": len(rows),
            "archive_gate_count_filtered": len(filtered),
            "archive_gate_count_returned": len(returned),
            "external_archive_manifest_artifact_count": len(archive_manifest_artifacts),
            "verified_archive_manifest_count": sum(1 for row in filtered if row.get("archive_status") == _VERIFIED_STATUS),
            "ready_for_archive_manifest_count": sum(1 for row in filtered if row.get("archive_status") == _READY_STATUS),
            "invalid_archive_manifest_count": sum(1 for row in filtered if row.get("archive_status") in {_INVALID_STATUS, _DIGEST_MISMATCH_STATUS}),
            "blocked_custody_count": sum(1 for row in filtered if row.get("archive_status") == _BLOCKED_STATUS),
            "archive_manifest_required_count": sum(1 for row in filtered if row.get("archive_manifest_required")),
            "archive_write_allowed_count": 0,
            "artifact_mutation_allowed_count": 0,
            "validator_submission_allowed_count": 0,
            "promotion_allowed_count": 0,
            "execution_allowed_count": 0,
            "source_custody_gate_count_total": (custody_payload.get("summary") or {}).get("custody_gate_count_total", 0),
            "source_recorded_custody_seal_count": (custody_payload.get("summary") or {}).get("recorded_custody_seal_count", 0),
            "latest_archive_gate_id": None if latest is None else latest.get("archive_gate_id"),
            "latest_archive_manifest_id": None if latest is None else latest.get("archive_manifest_id"),
            "latest_custody_gate_id": None if latest is None else latest.get("custody_gate_id"),
            "latest_decision_id": None if latest is None else latest.get("decision_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "archive_status_counts": _counts(filtered, "archive_status"),
        "trust_banner_counts": _counts(filtered, "trust_banner"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "degraded": degraded,
        "source_degraded": list(custody_payload.get("degraded") or []),
        "guardrails": ["read_plane_only_no_archive_write_or_artifact_mutation", "archive_manifests_must_be_created_by_external_human_workflow", "archive_matching_requires_packet_digest_continuity", "validator_submission_adjudication_promotion_and_execution_are_always_false", "verified_archive_manifest_is_evidence_only_not_release_promotion"],
        "latest": latest,
        "archive_gates": returned,
        "external_archive_manifest_artifacts": archive_manifest_artifacts,
    }


def build_ui_semantic_validator_handoff_archive_latest_payload(*, repo_root: str | Path | None = None, search_root: str | Path | None = None) -> dict[str, Any]:
    return build_ui_semantic_validator_handoff_archive_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = ["build_ui_semantic_validator_handoff_archive_payload", "build_ui_semantic_validator_handoff_archive_latest_payload"]
