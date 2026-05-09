"""Journal and submission receipt projections for the paper execution cockpit."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_cockpit_execution_common import (
    _as_dict,
    _mtime,
    _safe_read_json,
    _strings,
)
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401

def _submission_artifact_rows(repo_root: Path | None) -> list[tuple[Path, dict[str, Any], str]]:
    """Return durable paper submission artifacts newest-first.

    Guarded submissions write immutable history under ``submissions/*.json`` and
    a latest pointer at ``paper_order_submission.json``. Prefer immutable history
    when present, but keep compatibility with older workspaces that only have a
    latest pointer.
    """

    root = artifact_root_directory(repo_root) / "paper_broker"
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/submissions/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_order_submission.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[tuple[Path, dict[str, Any], str]] = []
    for path in sorted(candidates, key=_mtime, reverse=True)[:100]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
        rows.append((path, raw, digest))
    return rows


def _guard_status(value: Any) -> str:
    text = str(value or "UNKNOWN").upper()
    return text if text in {"PASS", "BLOCKED"} else "UNKNOWN"


def _freshness_status(value: Any) -> str:
    text = str(value or "UNKNOWN").upper()
    return text if text in {"FRESH", "STALE", "REPLAY_REQUIRED", "MISSING_EVIDENCE", "UNKNOWN"} else "UNKNOWN"


def _submission_receipts(repo_root: Path | None) -> list[PaperExecutionSubmissionReceiptView]:
    receipts: list[PaperExecutionSubmissionReceiptView] = []
    for path, raw, digest in _submission_artifact_rows(repo_root):
        default_tracking_id = path.parent.parent.name if path.parent.name == "submissions" else path.parent.name
        tracking_id = str(raw.get("tracking_id") or default_tracking_id)
        result = _as_dict(raw.get("result")) if raw.get("schema_version") == "paper_execution_submission_artifact/v1" else raw
        intent = _as_dict(raw.get("intent"))
        guard = _as_dict(raw.get("submission_guard"))
        result_warnings = _strings(result.get("warnings"))
        result_blockers = _strings(result.get("blockers"))
        guard_warnings = _strings(guard.get("warnings"))
        guard_blockers = _strings(guard.get("blockers"))
        receipts.append(
            PaperExecutionSubmissionReceiptView(
                tracking_id=tracking_id,
                artifact_path=str(path),
                artifact_sha256=digest,
                generated_at_utc=str(raw.get("generated_at_utc") or result.get("retrieved_at_utc") or "") or None,
                broker_order_id=str(result.get("broker_order_id")) if result.get("broker_order_id") else None,
                broker_status=str(result.get("status")) if result.get("status") else None,
                result_ok=bool(result.get("ok")) if result.get("ok") is not None else None,
                symbol=str(intent.get("symbol") or "").upper() or None,
                side=str(intent.get("side") or "").lower() or None,
                qty=float(intent.get("qty")) if intent.get("qty") is not None else None,
                filled_qty=float(result.get("filled_qty")) if result.get("filled_qty") is not None else None,
                policy_status=str(guard.get("policy_status") or result.get("policy_status") or "") or None,
                guard_status=_guard_status(guard.get("status")),  # type: ignore[arg-type]
                evidence_freshness_status=_freshness_status(guard.get("evidence_freshness_status")),  # type: ignore[arg-type]
                selected_intent_artifact_sha256=(
                    str(guard.get("selected_intent_artifact_sha256"))
                    if guard.get("selected_intent_artifact_sha256")
                    else None
                ),
                linked_dry_run_artifact_sha256=(
                    str(guard.get("linked_dry_run_artifact_sha256"))
                    if guard.get("linked_dry_run_artifact_sha256")
                    else None
                ),
                linked_dry_run_source_selection_sha256=(
                    str(guard.get("linked_dry_run_source_selection_sha256"))
                    if guard.get("linked_dry_run_source_selection_sha256")
                    else None
                ),
                submission_intent_matches_selection=(
                    bool(guard.get("submission_intent_matches_selection"))
                    if guard.get("submission_intent_matches_selection") is not None
                    else None
                ),
                linked_dry_run_matches_selection=(
                    bool(guard.get("linked_dry_run_matches_selection"))
                    if guard.get("linked_dry_run_matches_selection") is not None
                    else None
                ),
                linked_dry_run_ok=bool(guard.get("linked_dry_run_ok")) if guard.get("linked_dry_run_ok") is not None else None,
                guard_blocker_count=len(guard_blockers),
                guard_warning_count=len(guard_warnings),
                blockers=sorted(set(result_blockers + guard_blockers)),
                warnings=sorted(set(result_warnings + guard_warnings)),
            )
        )
    return sorted(receipts, key=lambda row: row.generated_at_utc or "", reverse=True)[:100]


def _journal_entries(repo_root: Path | None) -> list[PaperExecutionJournalEntry]:
    root = artifact_root_directory(repo_root) / "paper_broker"
    if not root.is_dir():
        return []

    entries: list[PaperExecutionJournalEntry] = []
    for path, raw, digest in _submission_artifact_rows(repo_root):
        default_tracking_id = path.parent.parent.name if path.parent.name == "submissions" else path.parent.name
        tracking_id = str(raw.get("tracking_id") or default_tracking_id)
        result = _as_dict(raw.get("result")) if raw.get("schema_version") == "paper_execution_submission_artifact/v1" else raw
        guard = _as_dict(raw.get("submission_guard"))
        guard_warnings = _strings(guard.get("warnings"))
        guard_blockers = _strings(guard.get("blockers"))
        entries.append(
            PaperExecutionJournalEntry(
                tracking_id=tracking_id,
                artifact_kind="SUBMISSION",
                artifact_path=str(path),
                broker_order_id=str(result.get("broker_order_id")) if result.get("broker_order_id") else None,
                status=str(result.get("status")) if result.get("status") else None,
                ok=bool(result.get("ok")) if result.get("ok") is not None else None,
                dry_run=bool(result.get("dry_run")) if result.get("dry_run") is not None else None,
                retrieved_at_utc=str(result.get("retrieved_at_utc") or raw.get("generated_at_utc") or "") or None,
                digest_prefix=digest[:16],
                source_selection_artifact_sha256=(
                    str(guard.get("selected_intent_artifact_sha256"))
                    if guard.get("selected_intent_artifact_sha256")
                    else None
                ),
                linked_dry_run_artifact_sha256=(
                    str(guard.get("linked_dry_run_artifact_sha256"))
                    if guard.get("linked_dry_run_artifact_sha256")
                    else None
                ),
                submission_guard_status=_guard_status(guard.get("status")),
                evidence_freshness_status=_freshness_status(guard.get("evidence_freshness_status")),
                selected_intent_match=guard.get("submission_intent_matches_selection")
                if guard.get("submission_intent_matches_selection") is not None
                else None,
                linked_dry_run_match=guard.get("linked_dry_run_matches_selection")
                if guard.get("linked_dry_run_matches_selection") is not None
                else None,
                linked_dry_run_ok=guard.get("linked_dry_run_ok")
                if guard.get("linked_dry_run_ok") is not None
                else None,
                warnings=_strings(result.get("warnings")) + guard_warnings,
                blockers=_strings(result.get("blockers")) + guard_blockers,
            )
        )

    dry_run_paths = list(root.glob("*/dry_runs/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in dry_run_paths if path.parent.parent.name}
    # Older workspaces may only have the latest pointer. Include it when no
    # immutable history exists for that tracking id.
    for latest_path in root.glob("*/paper_order_dry_run.json"):
        if latest_path.parent.name not in history_tracking_ids:
            dry_run_paths.append(latest_path)

    for path in sorted(dry_run_paths, key=_mtime, reverse=True)[:100]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        default_tracking_id = path.parent.parent.name if path.parent.name == "dry_runs" else path.parent.name
        tracking_id = str(raw.get("tracking_id") or default_tracking_id)
        result = _as_dict(raw.get("result"))
        digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
        entries.append(
            PaperExecutionJournalEntry(
                tracking_id=tracking_id,
                artifact_kind="DRY_RUN",
                artifact_path=str(path),
                broker_order_id=None,
                status="dry_run_ok" if result.get("ok") is True else "dry_run_blocked",
                ok=bool(result.get("ok")) if result.get("ok") is not None else None,
                dry_run=True,
                retrieved_at_utc=str(result.get("retrieved_at_utc") or raw.get("generated_at_utc") or "") or None,
                digest_prefix=digest[:16],
                source_selection_artifact_path=(
                    str(raw.get("source_selection_artifact_path"))
                    if raw.get("source_selection_artifact_path")
                    else None
                ),
                source_selection_artifact_sha256=(
                    str(raw.get("source_selection_artifact_sha256"))
                    if raw.get("source_selection_artifact_sha256")
                    else None
                ),
                warnings=_strings(result.get("warnings")),
                blockers=_strings(result.get("blockers")),
            )
        )
    return sorted(entries, key=lambda row: row.retrieved_at_utc or "", reverse=True)[:100]

__all__ = ["_journal_entries", "_submission_artifact_rows", "_submission_receipts"]
