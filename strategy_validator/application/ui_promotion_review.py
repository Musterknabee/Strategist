"""Read-plane projection for human-only promotion review packets.

This surface indexes existing ``promotion_review_packet.json`` artifacts under the
paper-tracking artifact tree. It never creates packets, mutates the ledger,
approves promotion, or grants execution authority.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import paper_tracking_root_directory
from strategy_validator.contracts.promotion_review_packet import PromotionReviewPacket

_SCHEMA_VERSION = "ui_promotion_review/v1"
_PACKET_NAME = "promotion_review_packet.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_root(repo_root: str | Path | None = None, paper_tracking_root: str | Path | None = None) -> Path:
    if paper_tracking_root is not None and str(paper_tracking_root).strip():
        p = Path(paper_tracking_root).expanduser()
        return p if p.is_absolute() else ((Path(repo_root) if repo_root else Path.cwd()) / p).resolve()
    return paper_tracking_root_directory(Path(repo_root) if repo_root else None)


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


def _issue_haystack(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    parts.extend(str(x) for x in entry.get("blockers") or [])
    parts.extend(str(x) for x in entry.get("warnings") or [])
    parts.extend(str(x) for x in entry.get("known_risks") or [])
    parts.append(str(entry.get("recommendation_rationale") or ""))
    return "\n".join(parts)


def _summary_line(packet: PromotionReviewPacket, blocker_count: int, warning_count: int) -> str:
    parts = [
        packet.strategy_id,
        f"tracking={packet.tracking_id}",
        f"state={packet.candidate_lifecycle_state}",
        f"rec={packet.recommendation.recommendation.value}",
    ]
    if blocker_count:
        parts.append(f"blockers={blocker_count}")
    if warning_count:
        parts.append(f"warnings={warning_count}")
    return " · ".join(parts)


def _packet_entry(path: Path, packet: PromotionReviewPacket, raw: dict[str, Any], *, include_raw: bool) -> dict[str, Any]:
    blockers = list(packet.blockers)
    warnings = list(packet.warnings)
    evidence_refs = [ref.model_dump(mode="json") for ref in packet.evidence_refs]
    checklist = packet.checklist.model_dump(mode="json")
    artifact_sha = _sha256(path)
    entry: dict[str, Any] = {
        "packet_id": packet.packet_id,
        "tracking_id": packet.tracking_id,
        "strategy_id": packet.strategy_id,
        "batch_id": packet.batch_id,
        "run_id": packet.run_id,
        "generated_at_utc": packet.generated_at_utc.isoformat(),
        "candidate_lifecycle_state": packet.candidate_lifecycle_state,
        "recommendation_status": packet.recommendation.recommendation.value,
        "recommendation_rationale": packet.recommendation.rationale,
        "blocker_count": len(blockers),
        "warning_count": len(warnings),
        "known_risk_count": len(packet.known_risks),
        "evidence_ref_count": len(evidence_refs),
        "checklist_pass_count": sum(1 for value in checklist.values() if value is True),
        "checklist_missing": [key for key, value in checklist.items() if value is False],
        "paper_days_of_signals": packet.paper_tracking_summary.get("days_of_signals"),
        "paper_kill_state": packet.paper_tracking_summary.get("kill_state"),
        "paper_cumulative_return": packet.paper_tracking_summary.get("cumulative_paper_return"),
        "kill_rule_posture": packet.kill_rule_summary.get("posture"),
        "portfolio_gate": packet.portfolio_correlation_summary.get("gate"),
        "provider_data_status": packet.provider_data_summary.get("status"),
        "packet_sha256": packet.packet_sha256,
        "artifact_sha256": artifact_sha,
        "artifact_path": str(path.as_posix()),
        "human_review_only_disclaimer": packet.human_review_only_disclaimer,
        "blockers": blockers,
        "warnings": warnings,
        "known_risks": list(packet.known_risks),
        "checklist": checklist,
        "recommendation": packet.recommendation.model_dump(mode="json"),
        "evidence_refs": evidence_refs,
        "summary_line": _summary_line(packet, len(blockers), len(warnings)),
    }
    if include_raw:
        entry["raw_packet"] = raw
    return entry


def _discover_packets(root: Path, *, include_raw: bool) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not root.is_dir():
        return [], []
    entries: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in sorted(root.glob(f"*/{_PACKET_NAME}")):
        raw = _read_json(path)
        if raw is None:
            invalid.append({"path": str(path.as_posix()), "reason": "invalid_json_or_not_object"})
            continue
        try:
            packet = PromotionReviewPacket.model_validate(raw)
        except ValueError as exc:
            invalid.append({"path": str(path.as_posix()), "reason": f"invalid_promotion_review_packet:{exc.__class__.__name__}"})
            continue
        entries.append(_packet_entry(path, packet, raw, include_raw=include_raw))
    entries.sort(key=lambda item: str(item.get("generated_at_utc") or ""), reverse=True)
    return entries, invalid


def _matches(
    entry: dict[str, Any],
    *,
    recommendations: set[str],
    lifecycle_states: set[str],
    tracking_id: str | None,
    strategy_id_contains: str | None,
    issue_contains: str | None,
    require_blockers: bool | None,
) -> bool:
    if recommendations and str(entry.get("recommendation_status") or "").upper() not in recommendations:
        return False
    if lifecycle_states and str(entry.get("candidate_lifecycle_state") or "").upper() not in lifecycle_states:
        return False
    if tracking_id and str(entry.get("tracking_id") or "") != tracking_id:
        return False
    if not _contains(entry.get("strategy_id"), strategy_id_contains):
        return False
    if issue_contains and not _contains(_issue_haystack(entry), issue_contains):
        return False
    blockers = int(entry.get("blocker_count") or 0)
    if require_blockers is True and blockers <= 0:
        return False
    if require_blockers is False and blockers > 0:
        return False
    return True


def _counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter[str(entry.get(field) or "UNKNOWN")] += 1
    return dict(sorted(counter.items()))


def build_ui_promotion_review_payload(
    *,
    repo_root: str | Path | None = None,
    paper_tracking_root: str | Path | None = None,
    recommendation: tuple[str, ...] = (),
    lifecycle_state: tuple[str, ...] = (),
    tracking_id: str | None = None,
    strategy_id_contains: str | None = None,
    issue_contains: str | None = None,
    require_blockers: bool | None = None,
    limit: int = 200,
    include_raw: bool = False,
) -> dict[str, Any]:
    root = _coerce_root(repo_root=repo_root, paper_tracking_root=paper_tracking_root)
    entries, invalid = _discover_packets(root, include_raw=include_raw)
    rec_filter = _norm_set(recommendation)
    state_filter = _norm_set(lifecycle_state)
    filtered = [
        entry
        for entry in entries
        if _matches(
            entry,
            recommendations=rec_filter,
            lifecycle_states=state_filter,
            tracking_id=tracking_id,
            strategy_id_contains=strategy_id_contains,
            issue_contains=issue_contains,
            require_blockers=require_blockers,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    blocked_count = sum(1 for entry in filtered if int(entry.get("blocker_count") or 0) > 0)
    warning_count = sum(int(entry.get("warning_count") or 0) for entry in filtered)
    evidence_ref_count = sum(int(entry.get("evidence_ref_count") or 0) for entry in filtered)
    ready_count = sum(1 for entry in filtered if entry.get("recommendation_status") == "READY_FOR_HUMAN_REVIEW")
    extension_count = sum(1 for entry in filtered if entry.get("recommendation_status") == "REVIEW_FOR_PAPER_EXTENSION")
    do_not_promote_count = sum(1 for entry in filtered if entry.get("recommendation_status") == "DO_NOT_PROMOTE")
    latest = returned[0] if returned else None
    degraded: list[str] = []
    if invalid:
        degraded.append("INVALID_PROMOTION_REVIEW_PACKET_ARTIFACTS_PRESENT")
    if not entries:
        degraded.append("NO_PROMOTION_REVIEW_PACKETS_FOUND")
    if blocked_count:
        degraded.append("PROMOTION_REVIEW_BLOCKERS_PRESENT")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "promotion_authority": "none_read_plane_human_review_only",
        "execution_authority": "none_read_plane",
        "paper_tracking_root": str(root.as_posix()),
        "filters": {
            "recommendation": list(rec_filter),
            "lifecycle_state": list(state_filter),
            "tracking_id": tracking_id,
            "strategy_id_contains": strategy_id_contains,
            "issue_contains": issue_contains,
            "require_blockers": require_blockers,
            "limit": capped_limit,
            "include_raw": include_raw,
        },
        "summary": {
            "packet_count_total": len(entries),
            "packet_count_filtered": len(filtered),
            "packet_count_returned": len(returned),
            "invalid_artifact_count": len(invalid),
            "ready_for_human_review_count": ready_count,
            "review_for_paper_extension_count": extension_count,
            "do_not_promote_count": do_not_promote_count,
            "blocked_packet_count": blocked_count,
            "warning_count_total": warning_count,
            "evidence_ref_count_total": evidence_ref_count,
            "latest_generated_at_utc": latest.get("generated_at_utc") if latest else None,
        },
        "recommendation_counts": _counts(filtered, "recommendation_status"),
        "lifecycle_state_counts": _counts(filtered, "candidate_lifecycle_state"),
        "portfolio_gate_counts": _counts(filtered, "portfolio_gate"),
        "kill_rule_posture_counts": _counts(filtered, "kill_rule_posture"),
        "degraded": degraded,
        "invalid_artifacts": invalid,
        "latest": latest,
        "packets": returned,
        "guardrails": [
            "Read-plane only: indexes existing promotion_review_packet.json artifacts.",
            "Human review only: no strategy promotion, adjudication, broker order, or live-execution authority is granted.",
            "Packet recommendations are evidence triage labels, not deployment approval.",
        ],
    }


def build_ui_promotion_review_latest_payload(
    *,
    repo_root: str | Path | None = None,
    paper_tracking_root: str | Path | None = None,
) -> dict[str, Any]:
    return build_ui_promotion_review_payload(repo_root=repo_root, paper_tracking_root=paper_tracking_root, limit=1)


__all__ = ["build_ui_promotion_review_payload", "build_ui_promotion_review_latest_payload"]
