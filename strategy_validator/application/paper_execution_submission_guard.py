"""Fail-closed paper submission guard and durable submission evidence writer."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_intent_selection import read_paper_execution_intent_selection_artifact
from strategy_validator.brokers.alpaca_paper import evaluate_alpaca_paper_policy
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult
from strategy_validator.contracts.paper_execution import (
    PaperExecutionSubmissionArtifact,
    PaperExecutionSubmissionGuardSnapshot,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_MAX_SELECTED_INTENT_AGE_HOURS = 24
_MAX_LINKED_DRY_RUN_AGE_HOURS = 12


def _paper_broker_root(output_root: Path | None = None) -> Path:
    root = output_root if output_root is not None else Path.cwd() / "artifacts" / "paper_broker"
    return root.expanduser().resolve()


def _safe_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _parse_time(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        dt = value
    else:
        text = str(value or "").strip()
        if not text:
            return None
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def _age_hours(now: datetime, value: Any) -> float | None:
    dt = _parse_time(value)
    if dt is None:
        return None
    return round(max(0.0, (now.astimezone(timezone.utc) - dt).total_seconds() / 3600.0), 4)


def _intent_signature(intent: PaperBrokerOrderIntent | dict[str, Any]) -> dict[str, Any]:
    raw = intent.model_dump(mode="json") if isinstance(intent, PaperBrokerOrderIntent) else dict(intent)
    return {
        "tracking_id": str(raw.get("tracking_id") or ""),
        "symbol": str(raw.get("symbol") or "").upper(),
        "side": str(raw.get("side") or "").lower(),
        "qty": float(raw.get("qty") or 0),
        "order_type": str(raw.get("order_type") or "market").lower(),
        "time_in_force": str(raw.get("time_in_force") or "day").lower(),
        "limit_price": raw.get("limit_price"),
    }


def _dry_run_event_time(raw: dict[str, Any]) -> str | None:
    result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
    return str(result.get("retrieved_at_utc") or raw.get("generated_at_utc") or "") or None


def _latest_linked_dry_run(
    *,
    tracking_id: str,
    selected_sha: str,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    tracking_dir = _paper_broker_root(output_root) / tracking_id
    candidates = list((tracking_dir / "dry_runs").glob("*.json"))
    latest = tracking_dir / "paper_order_dry_run.json"
    if latest.exists():
        candidates.append(latest)

    rows: list[tuple[datetime, Path, dict[str, Any]]] = []
    for path in candidates:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        if str(raw.get("source_selection_artifact_sha256") or "").strip() != selected_sha:
            continue
        when = _parse_time(_dry_run_event_time(raw)) or datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        rows.append((when, path, raw))
    if not rows:
        return None, None
    rows.sort(key=lambda row: row[0], reverse=True)
    return rows[0][1], rows[0][2]


def build_paper_submission_guard_snapshot(
    *,
    intent: PaperBrokerOrderIntent,
    env: dict[str, str],
    output_root: Path | None = None,
    evaluated_at_utc: datetime | None = None,
) -> PaperExecutionSubmissionGuardSnapshot:
    """Evaluate whether a CLI paper submission is backed by fresh evidence."""

    now = evaluated_at_utc or datetime.now(timezone.utc)
    policy, policy_warnings, policy_blockers = evaluate_alpaca_paper_policy(env)
    blockers: list[str] = list(policy_blockers)
    warnings: list[str] = list(policy_warnings)

    selection_path, selection = read_paper_execution_intent_selection_artifact(
        tracking_id=intent.tracking_id,
        output_root=output_root,
    )
    selected_sha = str((selection or {}).get("artifact_sha256") or "").strip() or None
    selected_age = _age_hours(now, (selection or {}).get("generated_at_utc")) if selection else None
    submission_matches = False
    if selection is None:
        blockers.append("SELECTED_INTENT_ARTIFACT_NOT_FOUND")
    else:
        selected_intent = selection.get("broker_intent") if isinstance(selection.get("broker_intent"), dict) else {}
        submission_matches = _intent_signature(intent) == _intent_signature(selected_intent)
        if not submission_matches:
            blockers.append("SUBMISSION_INTENT_MISMATCH_SELECTED_INTENT")
        if selected_age is None:
            blockers.append("SELECTED_INTENT_TIMESTAMP_MISSING")
        elif selected_age > _MAX_SELECTED_INTENT_AGE_HOURS:
            blockers.append("SELECTED_INTENT_STALE")

    dry_path: Path | None = None
    dry_raw: dict[str, Any] | None = None
    dry_sha: str | None = None
    dry_source_sha: str | None = None
    dry_age: float | None = None
    dry_matches = False
    dry_ok = False
    if selected_sha:
        dry_path, dry_raw = _latest_linked_dry_run(
            tracking_id=intent.tracking_id,
            selected_sha=selected_sha,
            output_root=output_root,
        )
        if dry_raw is None:
            blockers.append("LINKED_DRY_RUN_ARTIFACT_NOT_FOUND")
        else:
            dry_sha = str(dry_raw.get("artifact_sha256") or canonical_json_sha256(dry_raw))
            dry_source_sha = str(dry_raw.get("source_selection_artifact_sha256") or "").strip() or None
            dry_matches = dry_source_sha == selected_sha
            if not dry_matches:
                blockers.append("LINKED_DRY_RUN_SELECTION_SHA_MISMATCH")
            result = dry_raw.get("result") if isinstance(dry_raw.get("result"), dict) else {}
            dry_ok = bool(result.get("ok")) and bool(result.get("dry_run"))
            if not dry_ok:
                blockers.append("LINKED_DRY_RUN_NOT_OK")
            if result.get("blockers"):
                blockers.append("LINKED_DRY_RUN_HAS_BLOCKERS")
            dry_age = _age_hours(now, _dry_run_event_time(dry_raw))
            if dry_age is None:
                blockers.append("LINKED_DRY_RUN_TIMESTAMP_MISSING")
            elif dry_age > _MAX_LINKED_DRY_RUN_AGE_HOURS:
                blockers.append("LINKED_DRY_RUN_STALE")

    if policy.value != "PAPER_READY":
        blockers.append("PAPER_BROKER_POLICY_NOT_READY")

    uniq_blockers = sorted(set(blockers))
    status = "PASS" if not uniq_blockers else "BLOCKED"
    if not selection:
        freshness_status = "MISSING_EVIDENCE"
    elif dry_raw is None or not dry_matches:
        freshness_status = "REPLAY_REQUIRED"
    elif selected_age is not None and selected_age > _MAX_SELECTED_INTENT_AGE_HOURS:
        freshness_status = "STALE"
    elif dry_age is not None and dry_age > _MAX_LINKED_DRY_RUN_AGE_HOURS:
        freshness_status = "STALE"
    elif dry_ok and status == "PASS":
        freshness_status = "FRESH"
    else:
        freshness_status = "UNKNOWN"

    return PaperExecutionSubmissionGuardSnapshot(
        evaluated_at_utc=now,
        tracking_id=intent.tracking_id,
        status=status,  # type: ignore[arg-type]
        policy_status=policy.value,
        selected_intent_artifact_path=str(selection_path) if selection_path is not None else None,
        selected_intent_artifact_sha256=selected_sha,
        linked_dry_run_artifact_path=str(dry_path) if dry_path is not None else None,
        linked_dry_run_artifact_sha256=dry_sha,
        linked_dry_run_source_selection_sha256=dry_source_sha,
        selected_intent_age_hours=selected_age,
        linked_dry_run_age_hours=dry_age,
        evidence_freshness_status=freshness_status,  # type: ignore[arg-type]
        submission_intent_matches_selection=submission_matches,
        linked_dry_run_matches_selection=dry_matches,
        linked_dry_run_ok=dry_ok,
        blockers=uniq_blockers,
        warnings=sorted(set(warnings)),
    )


def build_paper_order_submission_artifact(
    *,
    intent: PaperBrokerOrderIntent,
    result: PaperBrokerOrderResult,
    guard_snapshot: PaperExecutionSubmissionGuardSnapshot,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionSubmissionArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    artifact = PaperExecutionSubmissionArtifact(
        generated_at_utc=now,
        tracking_id=intent.tracking_id,
        intent=intent.model_dump(mode="json"),
        result=result.model_dump(mode="json"),
        submission_guard=guard_snapshot,
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_order_submission_artifact(
    *,
    intent: PaperBrokerOrderIntent,
    result: PaperBrokerOrderResult,
    guard_snapshot: PaperExecutionSubmissionGuardSnapshot,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionSubmissionArtifact]:
    artifact = build_paper_order_submission_artifact(
        intent=intent,
        result=result,
        guard_snapshot=guard_snapshot,
        generated_at_utc=generated_at_utc,
    )
    tracking_dir = _paper_broker_root(output_root) / intent.tracking_id
    history_dir = tracking_dir / "submissions"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = tracking_dir / "paper_order_submission.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


__all__ = [
    "build_paper_order_submission_artifact",
    "build_paper_submission_guard_snapshot",
    "write_paper_order_submission_artifact",
]
