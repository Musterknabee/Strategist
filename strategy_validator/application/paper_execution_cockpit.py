"""Paper execution cockpit read model (no browser/API order submission)."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_cockpit_evidence_lifecycle import (
    build_paper_execution_evidence_lifecycle_projection,
)
from strategy_validator.application.paper_execution_cockpit_execution_state import (
    _as_dict,
    _broker_status,
    _build_intent_preview,
    _dry_run,
    _execution_timeline,
    _freshness_gate,
    _intent_selection_count,
    _journal_entries,
    _selected_artifact_to_preview,
    _selected_dry_run_replay_status,
    _selection_artifact,
    _submission_receipts,
)
from strategy_validator.application.paper_execution_cockpit_recommendations import _recommended_actions
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401

_SCHEMA = "ui_paper_execution_cockpit/v1"


def build_ui_paper_execution_cockpit_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    broker, broker_artifact_path, degraded = _broker_status(repo_root)
    _, latest_tracking = discover_latest_paper_tracking(repo_root=repo_root)
    tracking_present = latest_tracking is not None
    intents: list[PaperExecutionIntentPreview] = []
    dry_runs: list[dict[str, Any]] = []
    selected_raw, selected_count = _intent_selection_count(repo_root)
    selected_artifact = _selection_artifact(selected_raw)
    selected_preview = _selected_artifact_to_preview(selected_raw or {}) if selected_raw else None
    env = {k: str(v) for k, v in os.environ.items()}
    inferred_intent: PaperExecutionIntentPreview | None = None
    if latest_tracking is not None:
        inferred_intent = _build_intent_preview(latest_tracking)
    else:
        degraded.append("NO_PAPER_TRACKING_BUNDLE")
    if selected_preview is not None:
        intents.append(selected_preview)
    if inferred_intent is not None and (selected_preview is None or inferred_intent.tracking_id != selected_preview.tracking_id):
        intents.append(inferred_intent)
    dry_target = selected_preview or inferred_intent
    if dry_target is not None:
        dry_runs.append(_dry_run(dry_target, env))
    journal = _journal_entries(repo_root)
    submission_receipts = _submission_receipts(repo_root)
    dry_run_artifacts = [row for row in journal if row.artifact_kind == "DRY_RUN"]
    submission_artifacts = [row for row in journal if row.artifact_kind == "SUBMISSION"]
    latest_submission_receipt = submission_receipts[0] if submission_receipts else None
    submission_guard_blocker_count = sum(row.guard_blocker_count for row in submission_receipts)
    order_statuses = read_paper_order_status_views(repo_root=repo_root)
    latest_order_status = order_statuses[0] if order_statuses else None
    order_status_blocker_count = sum(len(row.blockers) for row in order_statuses)
    position_snapshot_path, position_snapshot = read_latest_paper_account_position_snapshot(repo_root=repo_root)
    position_reconciliation = build_paper_position_reconciliation_view(
        latest_submission_receipt=latest_submission_receipt,
        account_position_snapshot_path=position_snapshot_path,
        account_position_snapshot=position_snapshot,
        latest_order_status=latest_order_status,
        now=now,
    )
    execution_timeline, execution_timeline_summary = _execution_timeline(
        selected_raw=selected_raw,
        dry_run_artifacts=dry_run_artifacts,
        submission_receipts=submission_receipts,
        order_statuses=order_statuses,
        position_snapshot_path=position_snapshot_path,
        position_snapshot=position_snapshot,
        position_reconciliation=position_reconciliation,
    )
    evidence_lifecycle = build_paper_execution_evidence_lifecycle_projection(
        repo_root=repo_root,
        now=now,
        execution_timeline=execution_timeline,
        execution_timeline_summary=execution_timeline_summary,
    )
    replay_status, replay_match, replay_source_sha = _selected_dry_run_replay_status(
        selected_raw=selected_raw,
        dry_run_artifacts=dry_run_artifacts,
    )
    freshness_gate = _freshness_gate(
        now=now,
        selected_raw=selected_raw,
        latest_tracking=latest_tracking,
        broker=broker,
        dry_run_artifacts=dry_run_artifacts,
        replay_status=replay_status,
    )
    dry_ok = sum(1 for row in dry_runs if bool(row.get("ok")))
    dry_blocked = sum(1 for row in dry_runs if not bool(row.get("ok")))
    broker_policy = str(broker.get("policy_status") or "UNKNOWN")
    candidate = _as_dict(_as_dict(_as_dict(latest_tracking or {}).get("manifest")).get("candidate"))
    summary = PaperExecutionSummary(
        broker_policy_status=broker_policy,
        latest_tracking_id=str((latest_tracking or {}).get('tracking_id') or '') or None,
        latest_strategy_id=str(candidate.get('strategy_id') or '') or None,
        candidate_intent_count=len(intents),
        dry_run_ok_count=dry_ok,
        dry_run_blocked_count=dry_blocked,
        journal_entry_count=len(journal),
        dry_run_artifact_count=len(dry_run_artifacts),
        submission_artifact_count=len(submission_artifacts),
        submission_receipt_count=len(submission_receipts),
        latest_submission_receipt_at_utc=latest_submission_receipt.generated_at_utc if latest_submission_receipt else None,
        latest_submission_guard_status=latest_submission_receipt.guard_status if latest_submission_receipt else None,
        latest_submission_evidence_freshness_status=latest_submission_receipt.evidence_freshness_status if latest_submission_receipt else None,
        latest_submission_broker_order_id=latest_submission_receipt.broker_order_id if latest_submission_receipt else None,
        submission_guard_blocker_count=submission_guard_blocker_count,
        position_snapshot_count=1 if position_snapshot is not None else 0,
        latest_position_snapshot_at_utc=position_snapshot.generated_at_utc.isoformat() if position_snapshot else None,
        order_status_artifact_count=len(order_statuses),
        latest_order_status_at_utc=latest_order_status.generated_at_utc if latest_order_status else None,
        latest_order_status=latest_order_status.status if latest_order_status else None,
        latest_order_status_broker_order_id=latest_order_status.broker_order_id if latest_order_status else None,
        latest_order_status_filled_qty=latest_order_status.filled_qty if latest_order_status else None,
        order_status_blocker_count=order_status_blocker_count,
        position_reconciliation_status=position_reconciliation.status,
        position_reconciliation_blocker_count=position_reconciliation.reconciliation_blocker_count,
        position_reconciliation_warning_count=position_reconciliation.reconciliation_warning_count,
        latest_reconciled_symbol=position_reconciliation.symbol,
        latest_reconciled_position_qty=position_reconciliation.observed_position_qty,
        timeline_event_count=execution_timeline_summary.event_count,
        timeline_stage_count=execution_timeline_summary.stage_count,
        timeline_blocker_count=execution_timeline_summary.blocker_count,
        timeline_warning_count=execution_timeline_summary.warning_count,
        timeline_trusted_event_count=execution_timeline_summary.trusted_event_count,
        latest_timeline_event_at_utc=execution_timeline_summary.latest_event_at_utc,
        timeline_sequence_status=execution_timeline_summary.sequence_status,
        **evidence_lifecycle.summary_kwargs,
        latest_dry_run_artifact_at_utc=next((row.retrieved_at_utc for row in dry_run_artifacts if row.retrieved_at_utc), None),
        latest_dry_run_source_selection_sha256=replay_source_sha,
        selected_intent_dry_run_match=replay_match,
        selected_intent_dry_run_status=replay_status,
        selected_intent_count=selected_count,
        latest_selected_tracking_id=str((selected_raw or {}).get('tracking_id') or '') or None,
        latest_selected_intent_at_utc=str((selected_raw or {}).get('generated_at_utc') or '') or None,
        selected_intent_artifact_path=str((selected_raw or {}).get('artifact_path') or '') or None,
        broker_ready=broker_policy == 'PAPER_READY',
        tracking_present=tracking_present,
        paper_submission_capability='CLI_ONLY',
        evidence_freshness_status=freshness_gate.status,
        evidence_freshness_blocker_count=len(freshness_gate.blockers),
        selected_intent_age_hours=freshness_gate.selected_intent_age_hours,
        latest_linked_dry_run_age_hours=freshness_gate.latest_linked_dry_run_age_hours,
        latest_tracking_signal_age_hours=freshness_gate.latest_tracking_signal_age_hours,
    )
    actions = _recommended_actions(
        broker_policy=broker_policy,
        tracking_present=tracking_present,
        intent_count=len(intents),
        selected_count=selected_count,
        blocked_count=dry_blocked,
        journal_count=len(journal),
        replay_status=replay_status,
        freshness_gate=freshness_gate,
        submission_receipt_count=len(submission_receipts),
        submission_guard_blocker_count=submission_guard_blocker_count,
        latest_submission_guard_status=latest_submission_receipt.guard_status if latest_submission_receipt else None,
        position_reconciliation=position_reconciliation,
        order_statuses=order_statuses,
        timeline_summary=execution_timeline_summary,
        **evidence_lifecycle.action_kwargs,
    )
    payload = PaperExecutionCockpitPayload(
        generated_at_utc=now,
        scan_root=str(artifact_root_directory(repo_root)),
        broker_artifact_path=broker_artifact_path,
        degraded=sorted(set(degraded)),
        summary=summary,
        broker_status=broker,
        latest_tracking=latest_tracking,
        candidate_intents=intents,
        selected_intent=selected_artifact,
        dry_run_command_hint=str((selected_raw or {}).get('dry_run_command_hint') or '') or None,
        dry_run_results=dry_runs,
        freshness_gate=freshness_gate,
        journal_entries=journal,
        submission_receipts=submission_receipts,
        order_statuses=order_statuses,
        account_position_snapshot=position_snapshot,
        position_reconciliation=position_reconciliation,
        execution_timeline=execution_timeline,
        execution_timeline_summary=execution_timeline_summary,
        **evidence_lifecycle.payload_kwargs,
        recommended_actions=actions,
    )
    return payload.model_dump(mode="json")


__all__ = ["build_ui_paper_execution_cockpit_payload"]
