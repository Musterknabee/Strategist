"""Freshness and replay checks for the paper execution cockpit."""
from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Any

from strategy_validator.application.paper_execution_cockpit_execution_common import _as_dict
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401

def _selected_dry_run_replay_status(
    *,
    selected_raw: dict[str, Any] | None,
    dry_run_artifacts: list[PaperExecutionJournalEntry],
) -> tuple[str, bool | None, str | None]:
    """Compare newest selected-intent SHA with latest linked dry-run evidence."""

    selected_sha = str((selected_raw or {}).get("artifact_sha256") or "").strip()
    if not selected_sha:
        return "NO_SELECTED_INTENT", None, None
    if not dry_run_artifacts:
        return "NO_DRY_RUN", None, None
    latest_linked = next((row for row in dry_run_artifacts if row.source_selection_artifact_sha256), None)
    if latest_linked is None:
        return "NO_DRY_RUN", None, None
    source_sha = str(latest_linked.source_selection_artifact_sha256 or "").strip() or None
    matched = source_sha == selected_sha
    return ("MATCHED" if matched else "MISMATCHED"), matched, source_sha


def _parse_time(value: Any) -> datetime | None:
    """Parse common artifact timestamps as timezone-aware UTC datetimes."""

    if isinstance(value, datetime):
        dt = value
    elif isinstance(value, date):
        dt = datetime.combine(value, time.min)
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            if len(text) == 10 and text[4] == "-" and text[7] == "-":
                dt = datetime.fromisoformat(text + "T00:00:00+00:00")
            else:
                dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_hours(now: datetime, value: Any) -> tuple[float | None, str | None]:
    dt = _parse_time(value)
    if dt is None:
        return None, None
    age = max(0.0, (now.astimezone(timezone.utc) - dt).total_seconds() / 3600.0)
    return round(age, 4), dt.isoformat()


def _latest_tracking_signal_time(latest_tracking: dict[str, Any] | None) -> str | None:
    if not latest_tracking:
        return None
    recent = latest_tracking.get("signal_history_recent")
    if isinstance(recent, list) and recent:
        for row in reversed(recent):
            summary = _as_dict(_as_dict(row).get("summary"))
            for key in ("retrieved_at_utc", "generated_at_utc", "observation_datetime_utc", "observation_date_utc"):
                value = summary.get(key)
                if value:
                    return str(value)
    manifest = _as_dict(latest_tracking.get("manifest"))
    for key in ("created_at_utc", "generated_at_utc", "enrolled_at_utc"):
        value = manifest.get(key)
        if value:
            return str(value)
    candidate = _as_dict(manifest.get("candidate"))
    return str(candidate.get("enrolled_at_utc") or "") or None


def _freshness_gate(
    *,
    now: datetime,
    selected_raw: dict[str, Any] | None,
    latest_tracking: dict[str, Any] | None,
    broker: dict[str, Any],
    dry_run_artifacts: list[PaperExecutionJournalEntry],
    replay_status: str,
) -> PaperExecutionFreshnessGate:
    """Classify whether paper execution evidence is fresh enough to trust."""

    max_selected = 24
    max_dry_run = 12
    max_tracking = 48
    max_broker = 24
    warnings: list[str] = []
    blockers: list[str] = []
    stale: list[str] = []

    selected_sha = str((selected_raw or {}).get("artifact_sha256") or "").strip()
    selected_age, selected_at = _age_hours(now, (selected_raw or {}).get("generated_at_utc"))
    broker_age, broker_at = _age_hours(now, broker.get("generated_at_utc") or broker.get("retrieved_at_utc"))
    tracking_signal_at_raw = _latest_tracking_signal_time(latest_tracking)
    tracking_age, tracking_at = _age_hours(now, tracking_signal_at_raw)

    linked_entry: PaperExecutionJournalEntry | None = None
    if selected_sha:
        linked_entry = next(
            (
                row
                for row in dry_run_artifacts
                if str(row.source_selection_artifact_sha256 or "").strip() == selected_sha
            ),
            None,
        )
    if linked_entry is None:
        linked_entry = next((row for row in dry_run_artifacts if row.source_selection_artifact_sha256), None)
    dry_age, dry_at = _age_hours(now, linked_entry.retrieved_at_utc if linked_entry else None)

    if not selected_sha:
        blockers.append("SELECTED_INTENT_MISSING")
    if selected_sha and replay_status in {"NO_DRY_RUN", "MISMATCHED"}:
        blockers.append(f"SELECTED_INTENT_REPLAY_{replay_status}")
    if selected_age is None and selected_sha:
        blockers.append("SELECTED_INTENT_TIMESTAMP_MISSING")
    elif selected_age is not None and selected_age > max_selected:
        stale.append("SELECTED_INTENT_STALE")
        blockers.append("SELECTED_INTENT_STALE")
    if selected_sha and replay_status == "MATCHED":
        if dry_age is None:
            blockers.append("LINKED_DRY_RUN_TIMESTAMP_MISSING")
        elif dry_age > max_dry_run:
            stale.append("LINKED_DRY_RUN_STALE")
            blockers.append("LINKED_DRY_RUN_STALE")
    elif selected_sha and replay_status != "MATCHED":
        stale.append("LINKED_DRY_RUN_NOT_CURRENT")
    if latest_tracking is None:
        warnings.append("PAPER_TRACKING_BUNDLE_MISSING")
    elif tracking_age is None:
        warnings.append("PAPER_TRACKING_SIGNAL_TIMESTAMP_MISSING")
    elif tracking_age > max_tracking:
        stale.append("PAPER_TRACKING_SIGNAL_STALE")
        blockers.append("PAPER_TRACKING_SIGNAL_STALE")
    if broker_age is None:
        warnings.append("PAPER_BROKER_POLICY_TIMESTAMP_MISSING")
    elif broker_age > max_broker:
        stale.append("PAPER_BROKER_POLICY_STALE")
        blockers.append("PAPER_BROKER_POLICY_STALE")

    if not selected_sha or latest_tracking is None:
        status = "MISSING_EVIDENCE"
    elif replay_status in {"NO_DRY_RUN", "MISMATCHED"}:
        status = "REPLAY_REQUIRED"
    elif stale:
        status = "STALE"
    elif replay_status == "MATCHED":
        status = "FRESH"
    else:
        status = "UNKNOWN"

    return PaperExecutionFreshnessGate(
        status=status,  # type: ignore[arg-type]
        max_selected_intent_age_hours=max_selected,
        max_linked_dry_run_age_hours=max_dry_run,
        max_tracking_signal_age_hours=max_tracking,
        max_broker_policy_age_hours=max_broker,
        selected_intent_age_hours=selected_age,
        latest_linked_dry_run_age_hours=dry_age,
        latest_tracking_signal_age_hours=tracking_age,
        broker_policy_age_hours=broker_age,
        selected_intent_generated_at_utc=selected_at,
        latest_linked_dry_run_at_utc=dry_at,
        latest_tracking_signal_at_utc=tracking_at,
        broker_policy_generated_at_utc=broker_at,
        stale_reasons=sorted(set(stale)),
        warnings=sorted(set(warnings)),
        blockers=sorted(set(blockers)),
    )

__all__ = ["_freshness_gate", "_selected_dry_run_replay_status"]
