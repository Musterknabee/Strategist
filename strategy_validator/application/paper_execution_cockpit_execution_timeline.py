"""Execution timeline synthesis for the paper execution cockpit."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_cockpit_execution_common import _as_dict, _strings
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401

_STAGE_ORDER = {
    "SELECTED_INTENT": 10,
    "DRY_RUN": 20,
    "SUBMISSION": 30,
    "ORDER_STATUS": 40,
    "POSITION_SNAPSHOT": 50,
    "POSITION_RECONCILIATION": 60,
}
_REQUIRED_TIMELINE_STAGES = [
    "SELECTED_INTENT",
    "DRY_RUN",
    "SUBMISSION",
    "ORDER_STATUS",
    "POSITION_SNAPSHOT",
    "POSITION_RECONCILIATION",
]


def _timeline_entry_sort_key(entry: PaperExecutionTimelineEntry) -> tuple[str, int]:
    return (entry.generated_at_utc or "9999-12-31T23:59:59+00:00", entry.stage_order)


def _execution_timeline(
    *,
    selected_raw: dict[str, Any] | None,
    dry_run_artifacts: list[PaperExecutionJournalEntry],
    submission_receipts: list[PaperExecutionSubmissionReceiptView],
    order_statuses: list[PaperExecutionOrderStatusView],
    position_snapshot_path: Path | None,
    position_snapshot: Any | None,
    position_reconciliation: PaperExecutionPositionReconciliationView,
) -> tuple[list[PaperExecutionTimelineEntry], PaperExecutionTimelineSummary]:
    """Build a chronological, read-only audit trail for paper execution evidence."""

    entries: list[PaperExecutionTimelineEntry] = []
    if selected_raw:
        selected = _as_dict(selected_raw.get("selected_intent"))
        entries.append(
            PaperExecutionTimelineEntry(
                stage="SELECTED_INTENT",
                stage_order=_STAGE_ORDER["SELECTED_INTENT"],
                tracking_id=str(selected_raw.get("tracking_id") or selected.get("tracking_id") or "") or None,
                generated_at_utc=str(selected_raw.get("generated_at_utc") or "") or None,
                artifact_path=str(selected_raw.get("artifact_path") or "") or None,
                artifact_sha256=str(selected_raw.get("artifact_sha256") or "") or None,
                status="SELECTED",
                ok=True,
                trusted=True,
                summary_line="Operator selected a paper execution intent for CLI dry-run replay.",
                symbol=str(selected.get("symbol") or "").upper() or None,
                side=str(selected.get("side") or "").lower() or None,
                qty=float(selected.get("qty")) if selected.get("qty") is not None else None,
                warnings=_strings(selected.get("warnings")),
            )
        )

    for row in dry_run_artifacts:
        linked = bool(row.source_selection_artifact_sha256)
        blockers = list(row.blockers)
        warnings = list(row.warnings)
        if not linked:
            warnings.append("DRY_RUN_NOT_LINKED_TO_SELECTED_INTENT")
        entries.append(
            PaperExecutionTimelineEntry(
                stage="DRY_RUN",
                stage_order=_STAGE_ORDER["DRY_RUN"],
                tracking_id=row.tracking_id,
                generated_at_utc=row.retrieved_at_utc,
                artifact_path=row.artifact_path,
                artifact_sha256=row.digest_prefix,
                status=row.status or "UNKNOWN",
                ok=row.ok,
                trusted=bool(row.ok is True and linked and not blockers),
                summary_line=(
                    "Linked dry-run replay validated the selected paper intent."
                    if row.ok is True and linked and not blockers
                    else "Dry-run evidence requires review before submission trust."
                ),
                broker_order_id=row.broker_order_id,
                source_selection_artifact_sha256=row.source_selection_artifact_sha256,
                warnings=sorted(set(warnings)),
                blockers=sorted(set(blockers)),
            )
        )

    for receipt in submission_receipts:
        blockers = list(receipt.blockers)
        trusted = bool(receipt.guard_status == "PASS" and receipt.result_ok is True and not blockers)
        entries.append(
            PaperExecutionTimelineEntry(
                stage="SUBMISSION",
                stage_order=_STAGE_ORDER["SUBMISSION"],
                tracking_id=receipt.tracking_id,
                generated_at_utc=receipt.generated_at_utc,
                artifact_path=receipt.artifact_path,
                artifact_sha256=receipt.artifact_sha256,
                status=receipt.guard_status if receipt.guard_status != "UNKNOWN" else (receipt.broker_status or "UNKNOWN"),
                ok=receipt.result_ok,
                trusted=trusted,
                summary_line=(
                    "Guarded CLI-only paper submission receipt passed evidence preflight."
                    if trusted
                    else "Paper submission receipt has guard, freshness, or broker-result blockers."
                ),
                broker_order_id=receipt.broker_order_id,
                symbol=receipt.symbol,
                side=receipt.side,
                qty=receipt.qty,
                source_selection_artifact_sha256=receipt.selected_intent_artifact_sha256,
                linked_dry_run_artifact_sha256=receipt.linked_dry_run_artifact_sha256,
                warnings=receipt.warnings,
                blockers=blockers,
            )
        )

    for status in order_statuses:
        blockers = list(status.blockers)
        trusted = bool(status.ok is True and status.status in {"filled", "partially_filled"} and not blockers)
        entries.append(
            PaperExecutionTimelineEntry(
                stage="ORDER_STATUS",
                stage_order=_STAGE_ORDER["ORDER_STATUS"],
                tracking_id=status.tracking_id,
                generated_at_utc=status.generated_at_utc,
                artifact_path=status.artifact_path,
                artifact_sha256=status.artifact_sha256,
                status=status.status or "UNKNOWN",
                ok=status.ok,
                trusted=trusted,
                summary_line=(
                    "Broker order-status refresh confirms fill evidence."
                    if trusted
                    else "Broker order-status refresh does not yet prove a fill."
                ),
                broker_order_id=status.broker_order_id,
                symbol=status.symbol,
                side=status.side,
                qty=status.filled_qty,
                source_submission_artifact_sha256=status.source_submission_artifact_sha256,
                warnings=status.warnings,
                blockers=blockers,
            )
        )

    if position_snapshot is not None:
        entries.append(
            PaperExecutionTimelineEntry(
                stage="POSITION_SNAPSHOT",
                stage_order=_STAGE_ORDER["POSITION_SNAPSHOT"],
                tracking_id=position_reconciliation.tracking_id,
                generated_at_utc=position_snapshot.generated_at_utc.isoformat(),
                artifact_path=str(position_snapshot_path) if position_snapshot_path is not None else None,
                artifact_sha256=position_snapshot.artifact_sha256,
                status=str(position_snapshot.policy_status or "UNKNOWN"),
                ok=position_snapshot.policy_status == "PAPER_READY",
                trusted=bool(position_snapshot.policy_status == "PAPER_READY" and position_snapshot.position_count >= 0),
                summary_line="Paper account/position snapshot captured for broker-state reconciliation.",
                symbol=position_reconciliation.symbol,
                qty=position_reconciliation.observed_position_qty,
                warnings=list(position_snapshot.notes),
            )
        )

    if position_reconciliation.status != "NO_SUBMISSION":
        entries.append(
            PaperExecutionTimelineEntry(
                stage="POSITION_RECONCILIATION",
                stage_order=_STAGE_ORDER["POSITION_RECONCILIATION"],
                tracking_id=position_reconciliation.tracking_id,
                generated_at_utc=position_reconciliation.account_position_snapshot_at_utc
                or position_reconciliation.latest_submission_receipt_at_utc,
                artifact_path=position_reconciliation.account_position_snapshot_path,
                artifact_sha256=position_reconciliation.account_position_snapshot_sha256,
                status=position_reconciliation.status,
                ok=position_reconciliation.status == "RECONCILED",
                trusted=position_reconciliation.status == "RECONCILED" and position_reconciliation.reconciliation_blocker_count == 0,
                summary_line=(
                    "Position snapshot reconciles with filled paper execution evidence."
                    if position_reconciliation.status == "RECONCILED"
                    else "Position reconciliation is incomplete or blocked."
                ),
                symbol=position_reconciliation.symbol,
                side=position_reconciliation.side,
                qty=position_reconciliation.filled_qty,
                warnings=position_reconciliation.warnings,
                blockers=position_reconciliation.blockers,
            )
        )

    entries = sorted(entries, key=_timeline_entry_sort_key)
    stages = {entry.stage for entry in entries}
    completed = [stage for stage in _REQUIRED_TIMELINE_STAGES if stage in stages]
    missing = [stage for stage in _REQUIRED_TIMELINE_STAGES if stage not in stages]
    blocker_count = sum(len(entry.blockers) for entry in entries)
    warning_count = sum(len(entry.warnings) for entry in entries)
    trusted_count = sum(1 for entry in entries if entry.trusted)
    if not entries:
        sequence_status = "EMPTY"
    elif blocker_count:
        sequence_status = "BLOCKED"
    elif not missing and any(entry.stage == "POSITION_RECONCILIATION" and entry.trusted for entry in entries):
        sequence_status = "COMPLETE"
    else:
        sequence_status = "PARTIAL"
    summary = PaperExecutionTimelineSummary(
        event_count=len(entries),
        stage_count=len(stages),
        trusted_event_count=trusted_count,
        blocker_count=blocker_count,
        warning_count=warning_count,
        latest_event_at_utc=max((entry.generated_at_utc for entry in entries if entry.generated_at_utc), default=None),
        sequence_status=sequence_status,  # type: ignore[arg-type]
        completed_stages=completed,
        missing_stages=missing,
    )
    return entries[:100], summary

__all__ = ["_execution_timeline"]
