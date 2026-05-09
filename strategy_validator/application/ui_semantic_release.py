"""Read-plane cockpit for semantic adjudication release handoff artifacts.

This projection indexes existing semantic release index, capsule, and terminal
release-decision artifacts. It deliberately performs only file discovery and
self-verification; it never builds release artifacts, mutates the ledger, hands
anything to adjudication, or grants execution authority.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from strategy_validator.application.research_integrity_release_capsule import (
    summarize_semantic_adjudication_release_capsule,
    summarize_semantic_adjudication_release_decision_record,
    verify_semantic_adjudication_release_capsule,
    verify_semantic_adjudication_release_decision_record,
)
from strategy_validator.application.research_integrity_release_index import (
    verify_semantic_adjudication_bundle_release_index,
)
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseDecisionRecord,
)

_SCHEMA_VERSION = "ui_semantic_release_handoff/v1"
_KNOWN_SCHEMAS = {
    "semantic_adjudication_bundle_release_index/v1": "release_index",
    "semantic_adjudication_release_capsule/v1": "release_capsule",
    "semantic_adjudication_release_decision_record/v1": "decision_record",
}
_DEFAULT_RELATIVE_ROOTS = (
    Path("artifacts") / "research_integrity",
    Path("artifacts") / "semantic_release",
    Path("artifacts") / "research_release",
    Path("artifacts"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_root(repo_root: str | Path | None = None, search_root: str | Path | None = None) -> Path:
    base = Path(repo_root).expanduser() if repo_root else Path.cwd()
    if search_root is not None and str(search_root).strip():
        p = Path(search_root).expanduser()
        return p.resolve() if p.is_absolute() else (base / p).resolve()
    for relative in _DEFAULT_RELATIVE_ROOTS:
        candidate = (base / relative).resolve()
        if candidate.is_dir():
            return candidate
    return (base / _DEFAULT_RELATIVE_ROOTS[0]).resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _contains(value: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {str(v).strip().upper() for v in (values or ()) if str(v).strip()}


def _issue_codes_from_report(report: object) -> list[str]:
    value = getattr(report, "issue_codes", [])
    return [str(item) for item in value]


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _release_index_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(raw)
    report = verify_semantic_adjudication_bundle_release_index(index)
    preflight = index.release_preflight
    blocker_codes = list(dict.fromkeys([*preflight.blocker_codes, *[code for code in report.issue_codes if not report.verified]]))
    warning_codes = list(preflight.warning_codes)
    entry: dict[str, Any] = {
        "artifact_kind": "release_index",
        "schema_version": index.schema_version,
        "artifact_id": index.index_id,
        "index_id": index.index_id,
        "capsule_id": None,
        "decision_id": None,
        "bundle_id": index.bundle_id,
        "experiment_id": index.experiment_id,
        "proposal_digest": index.proposal_digest,
        "payload_checksum": index.payload_checksum,
        "artifact_sha256": _sha256(path),
        "artifact_path": str(path.as_posix()),
        "verified": report.verified,
        "ready_for_adjudication": preflight.ready_for_adjudication,
        "recommended_action": preflight.recommended_action if report.verified else report.recommended_action,
        "decision": None,
        "decision_allowed": None,
        "blocker_codes": blocker_codes,
        "warning_codes": warning_codes,
        "issue_codes": list(dict.fromkeys([*report.issue_codes, *blocker_codes, *warning_codes])),
        "issue_count": max(report.issue_count, len(blocker_codes) + len(warning_codes)),
        "semantic_evidence_count": len(index.semantic_evidence_checksums),
        "manifest_id": index.manifest_id,
        "gate_artifact_id": index.gate_artifact_id,
        "handoff_artifact_id": index.handoff_artifact_id,
        "data_spine_fingerprint_present": bool(index.data_spine_fingerprint),
        "summary_line": f"release_index · {index.experiment_id} · ready={preflight.ready_for_adjudication} · verified={report.verified}",
        "verification": report.model_dump(mode="json"),
        "release_preflight": preflight.model_dump(mode="json"),
    }
    if include_raw:
        entry["raw_artifact"] = raw
    return entry


def _release_capsule_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(raw)
    report = verify_semantic_adjudication_release_capsule(capsule)
    summary = summarize_semantic_adjudication_release_capsule(capsule, verification=report)
    blocker_codes = list(summary.blocker_codes)
    warning_codes = list(summary.warning_codes)
    entry: dict[str, Any] = {
        "artifact_kind": "release_capsule",
        "schema_version": capsule.schema_version,
        "artifact_id": capsule.capsule_id,
        "index_id": capsule.index_id,
        "capsule_id": capsule.capsule_id,
        "decision_id": None,
        "bundle_id": capsule.bundle_id,
        "experiment_id": capsule.experiment_id,
        "proposal_digest": capsule.proposal_digest,
        "payload_checksum": capsule.payload_checksum,
        "artifact_sha256": _sha256(path),
        "artifact_path": str(path.as_posix()),
        "verified": report.verified,
        "ready_for_adjudication": summary.ready_for_adjudication,
        "recommended_action": summary.recommended_action,
        "decision": None,
        "decision_allowed": None,
        "blocker_codes": blocker_codes,
        "warning_codes": warning_codes,
        "issue_codes": list(dict.fromkeys([*summary.capsule_issue_codes, *summary.index_issue_codes, *blocker_codes, *warning_codes])),
        "issue_count": summary.issue_count,
        "semantic_evidence_count": None,
        "manifest_id": None,
        "gate_artifact_id": None,
        "handoff_artifact_id": None,
        "data_spine_fingerprint_present": None,
        "summary_line": f"release_capsule · {capsule.experiment_id} · ready={summary.ready_for_adjudication} · verified={report.verified}",
        "verification": report.model_dump(mode="json"),
        "capsule_summary": summary.model_dump(mode="json"),
    }
    if include_raw:
        entry["raw_artifact"] = raw
    return entry


def _decision_record_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    record = SemanticAdjudicationReleaseDecisionRecord.model_validate(raw)
    report = verify_semantic_adjudication_release_decision_record(record)
    summary = summarize_semantic_adjudication_release_decision_record(record, verification=report)
    blocker_codes = list(summary.blocker_codes)
    warning_codes = list(summary.warning_codes)
    entry: dict[str, Any] = {
        "artifact_kind": "decision_record",
        "schema_version": record.schema_version,
        "artifact_id": record.decision_id,
        "index_id": record.index_id,
        "capsule_id": record.capsule_id,
        "decision_id": record.decision_id,
        "bundle_id": record.bundle_id,
        "experiment_id": record.experiment_id,
        "proposal_digest": record.proposal_digest,
        "payload_checksum": record.payload_checksum,
        "artifact_sha256": _sha256(path),
        "artifact_path": str(path.as_posix()),
        "verified": report.verified,
        "ready_for_adjudication": summary.capsule_ready_for_adjudication,
        "recommended_action": summary.recommended_action,
        "decision": record.decision,
        "decision_allowed": record.decision_allowed,
        "decided_by": record.decided_by,
        "decision_reason": record.decision_reason,
        "blocker_codes": blocker_codes,
        "warning_codes": warning_codes,
        "issue_codes": list(dict.fromkeys([*summary.record_issue_codes, *blocker_codes, *warning_codes])),
        "issue_count": summary.issue_count,
        "semantic_evidence_count": None,
        "manifest_id": None,
        "gate_artifact_id": None,
        "handoff_artifact_id": None,
        "data_spine_fingerprint_present": None,
        "summary_line": f"decision_record · {record.experiment_id} · decision={record.decision} · allowed={record.decision_allowed}",
        "verification": report.model_dump(mode="json"),
        "decision_summary": summary.model_dump(mode="json"),
    }
    if include_raw:
        entry["raw_artifact"] = raw
    return entry


def _artifact_entry(path: Path, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    schema = str(raw.get("schema_version") or "")
    if schema == "semantic_adjudication_bundle_release_index/v1":
        return _release_index_entry(path, raw, include_raw=include_raw)
    if schema == "semantic_adjudication_release_capsule/v1":
        return _release_capsule_entry(path, raw, include_raw=include_raw)
    if schema == "semantic_adjudication_release_decision_record/v1":
        return _decision_record_entry(path, raw, include_raw=include_raw)
    raise ValueError(f"unsupported_semantic_release_schema:{schema or 'missing'}")


def _discover(root: Path, *, include_raw: bool) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not root.exists():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_missing"}]
    if not root.is_dir():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_not_directory"}]
    entries: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in sorted(root.rglob("*.json")):
        raw = _read_json(path)
        if raw is None:
            # Only record invalid JSON when the filename looks release-related to avoid noisy whole-artifact scans.
            if "release" in path.name.lower() or "semantic" in path.name.lower():
                invalid.append({"path": str(path.as_posix()), "reason": "invalid_json_or_not_object"})
            continue
        schema = str(raw.get("schema_version") or "")
        if schema not in _KNOWN_SCHEMAS:
            continue
        try:
            entries.append(_artifact_entry(path, raw, include_raw=include_raw))
        except (ValidationError, ValueError) as exc:
            invalid.append({"path": str(path.as_posix()), "reason": f"invalid_semantic_release_artifact:{exc.__class__.__name__}"})
    entries.sort(key=lambda item: (str(item.get("experiment_id") or ""), str(item.get("artifact_kind") or ""), str(item.get("artifact_id") or "")), reverse=True)
    return entries, invalid


def _issue_haystack(entry: dict[str, Any]) -> str:
    parts = [str(entry.get("recommended_action") or ""), str(entry.get("summary_line") or "")]
    parts.extend(_as_list(entry.get("blocker_codes")))
    parts.extend(_as_list(entry.get("warning_codes")))
    parts.extend(_as_list(entry.get("issue_codes")))
    return "\n".join(parts)


def _matches(
    entry: dict[str, Any],
    *,
    artifact_kinds: set[str],
    recommended_actions: set[str],
    experiment_id_contains: str | None,
    bundle_id_contains: str | None,
    issue_contains: str | None,
    ready_for_adjudication: bool | None,
    verified: bool | None,
    require_blockers: bool | None,
) -> bool:
    if artifact_kinds and str(entry.get("artifact_kind") or "").upper() not in artifact_kinds:
        return False
    if recommended_actions and str(entry.get("recommended_action") or "").upper() not in recommended_actions:
        return False
    if not _contains(entry.get("experiment_id"), experiment_id_contains):
        return False
    if not _contains(entry.get("bundle_id"), bundle_id_contains):
        return False
    if issue_contains and not _contains(_issue_haystack(entry), issue_contains):
        return False
    if ready_for_adjudication is not None and bool(entry.get("ready_for_adjudication")) is not ready_for_adjudication:
        return False
    if verified is not None and bool(entry.get("verified")) is not verified:
        return False
    blocker_count = len(_as_list(entry.get("blocker_codes")))
    if require_blockers is True and blocker_count <= 0:
        return False
    if require_blockers is False and blocker_count > 0:
        return False
    return True


def _counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter[str(entry.get(field) if entry.get(field) is not None else "UNKNOWN")] += 1
    return dict(sorted(counter.items()))


def _bool_counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter["true" if bool(entry.get(field)) else "false"] += 1
    return dict(sorted(counter.items()))


def build_ui_semantic_release_handoff_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    artifact_kind: tuple[str, ...] = (),
    recommended_action: tuple[str, ...] = (),
    experiment_id_contains: str | None = None,
    bundle_id_contains: str | None = None,
    issue_contains: str | None = None,
    ready_for_adjudication: bool | None = None,
    verified: bool | None = None,
    require_blockers: bool | None = None,
    limit: int = 200,
    include_raw: bool = False,
) -> dict[str, Any]:
    root = _coerce_root(repo_root=repo_root, search_root=search_root)
    entries, invalid = _discover(root, include_raw=include_raw)
    kind_filter = _norm_set(artifact_kind)
    action_filter = _norm_set(recommended_action)
    filtered = [
        entry
        for entry in entries
        if _matches(
            entry,
            artifact_kinds=kind_filter,
            recommended_actions=action_filter,
            experiment_id_contains=experiment_id_contains,
            bundle_id_contains=bundle_id_contains,
            issue_contains=issue_contains,
            ready_for_adjudication=ready_for_adjudication,
            verified=verified,
            require_blockers=require_blockers,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    ready_count = sum(1 for entry in filtered if bool(entry.get("ready_for_adjudication")))
    verified_count = sum(1 for entry in filtered if bool(entry.get("verified")))
    blocked_count = sum(1 for entry in filtered if len(_as_list(entry.get("blocker_codes"))) > 0)
    decision_allowed_count = sum(1 for entry in filtered if bool(entry.get("decision_allowed")))
    release_index_count = sum(1 for entry in filtered if entry.get("artifact_kind") == "release_index")
    capsule_count = sum(1 for entry in filtered if entry.get("artifact_kind") == "release_capsule")
    decision_record_count = sum(1 for entry in filtered if entry.get("artifact_kind") == "decision_record")
    degraded: list[str] = []
    if invalid:
        degraded.append("INVALID_SEMANTIC_RELEASE_ARTIFACTS_PRESENT")
    if not entries:
        degraded.append("NO_SEMANTIC_RELEASE_HANDOFF_ARTIFACTS_FOUND")
    if blocked_count:
        degraded.append("SEMANTIC_RELEASE_BLOCKERS_PRESENT")
    if any(not bool(entry.get("verified")) for entry in filtered):
        degraded.append("SEMANTIC_RELEASE_SELF_VERIFICATION_FAILURES_PRESENT")
    latest = returned[0] if returned else None
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
        "search_root": str(root.as_posix()),
        "filters": {
            "artifact_kind": list(kind_filter),
            "recommended_action": list(action_filter),
            "experiment_id_contains": experiment_id_contains,
            "bundle_id_contains": bundle_id_contains,
            "issue_contains": issue_contains,
            "ready_for_adjudication": ready_for_adjudication,
            "verified": verified,
            "require_blockers": require_blockers,
            "limit": capped_limit,
            "include_raw": include_raw,
        },
        "summary": {
            "artifact_count_total": len(entries),
            "artifact_count_filtered": len(filtered),
            "artifact_count_returned": len(returned),
            "invalid_artifact_count": len(invalid),
            "release_index_count": release_index_count,
            "release_capsule_count": capsule_count,
            "decision_record_count": decision_record_count,
            "ready_for_adjudication_count": ready_count,
            "verified_artifact_count": verified_count,
            "blocked_artifact_count": blocked_count,
            "decision_allowed_count": decision_allowed_count,
            "latest_artifact_id": None if latest is None else latest.get("artifact_id"),
            "latest_experiment_id": None if latest is None else latest.get("experiment_id"),
        },
        "artifact_kind_counts": _counts(filtered, "artifact_kind"),
        "recommended_action_counts": _counts(filtered, "recommended_action"),
        "verified_counts": _bool_counts(filtered, "verified"),
        "ready_counts": _bool_counts(filtered, "ready_for_adjudication"),
        "decision_counts": _counts(filtered, "decision"),
        "degraded": degraded,
        "invalid_artifacts": invalid,
        "guardrails": [
            "read_plane_only_no_artifact_creation_or_mutation",
            "no_adjudication_or_validator_authority",
            "no_promotion_or_execution_authority",
            "self_verification_only_source_bundle_replay_not_performed",
            "artifact_presence_is_not_approval_or_live_readiness",
        ],
        "latest": latest,
        "artifacts": returned,
    }


def build_ui_semantic_release_handoff_latest_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_semantic_release_handoff_payload(repo_root=repo_root, search_root=search_root, limit=1)


__all__ = ["build_ui_semantic_release_handoff_payload", "build_ui_semantic_release_handoff_latest_payload"]
