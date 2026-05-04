"""Paper execution cockpit read model (no browser/API order submission)."""
from __future__ import annotations

import json
import os
from datetime import date, datetime, time, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import (
    artifact_root_directory,
    paper_broker_status_artifact_path,
)
from strategy_validator.application.paper_execution_evidence_bundle import read_paper_execution_evidence_bundle_views
from strategy_validator.application.paper_execution_evidence_bundle_verification import read_paper_execution_evidence_bundle_verification_views
from strategy_validator.application.paper_execution_evidence_bundle_drift import (
    build_paper_execution_evidence_bundle_drift_artifact,
    read_paper_execution_evidence_bundle_drift_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_rotation import (
    build_paper_execution_evidence_bundle_rotation_artifact,
    read_paper_execution_evidence_bundle_rotation_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_rotation_execution import (
    read_paper_execution_evidence_bundle_rotation_execution_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_attestation import (
    build_paper_execution_evidence_bundle_attestation_artifact,
    read_paper_execution_evidence_bundle_attestation_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import (
    read_paper_execution_evidence_bundle_attestation_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_closure import (
    _view_from_artifact as _closure_view_from_artifact,
    build_paper_execution_evidence_bundle_closure_artifact,
    read_paper_execution_evidence_bundle_closure_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_closure_verification import (
    read_paper_execution_evidence_bundle_closure_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_export import (
    read_paper_execution_evidence_bundle_export_manifest_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_export_verification import (
    read_paper_execution_evidence_bundle_export_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention import (
    read_paper_execution_evidence_bundle_retention_receipt_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_verification import (
    read_paper_execution_evidence_bundle_retention_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff import (
    read_paper_execution_evidence_bundle_retention_signoff_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff_verification import (
    read_paper_execution_evidence_bundle_retention_signoff_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import (
    read_paper_execution_evidence_bundle_retention_handoff_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_verification import (
    read_paper_execution_evidence_bundle_retention_handoff_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance import (
    read_paper_execution_evidence_bundle_retention_handoff_acceptance_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance_verification import (
    read_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import (
    read_paper_execution_evidence_bundle_retention_custody_register_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register_verification import (
    read_paper_execution_evidence_bundle_retention_custody_register_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal import (
    read_paper_execution_evidence_bundle_retention_custody_seal_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal_verification import (
    read_paper_execution_evidence_bundle_retention_custody_seal_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit import (
    read_paper_execution_evidence_bundle_retention_custody_audit_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit_verification import (
    read_paper_execution_evidence_bundle_retention_custody_audit_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity import (
    read_paper_execution_evidence_bundle_retention_custody_continuity_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity_verification import (
    read_paper_execution_evidence_bundle_retention_custody_continuity_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review import (
    read_paper_execution_evidence_bundle_retention_custody_review_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review_verification import (
    read_paper_execution_evidence_bundle_retention_custody_review_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal import (
    read_paper_execution_evidence_bundle_retention_custody_renewal_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal_verification import (
    read_paper_execution_evidence_bundle_retention_custody_renewal_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule import (
    read_paper_execution_evidence_bundle_retention_custody_schedule_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule_verification import (
    read_paper_execution_evidence_bundle_retention_custody_schedule_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice import (
    read_paper_execution_evidence_bundle_retention_custody_notice_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice_verification import (
    read_paper_execution_evidence_bundle_retention_custody_notice_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment import (
    read_paper_execution_evidence_bundle_retention_custody_acknowledgment_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment_verification import (
    read_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion import (
    read_paper_execution_evidence_bundle_retention_custody_completion_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion_verification import (
    read_paper_execution_evidence_bundle_retention_custody_completion_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout import (
    read_paper_execution_evidence_bundle_retention_custody_closeout_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout_verification import (
    read_paper_execution_evidence_bundle_retention_custody_closeout_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive import (
    read_paper_execution_evidence_bundle_retention_custody_archive_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive_verification import (
    read_paper_execution_evidence_bundle_retention_custody_archive_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval import (
    read_paper_execution_evidence_bundle_retention_custody_retrieval_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval_verification import (
    read_paper_execution_evidence_bundle_retention_custody_retrieval_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return import (
    read_paper_execution_evidence_bundle_retention_custody_return_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return_verification import (
    read_paper_execution_evidence_bundle_retention_custody_return_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit import (
    read_paper_execution_evidence_bundle_retention_custody_redeposit_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit_verification import (
    read_paper_execution_evidence_bundle_retention_custody_redeposit_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory import (
    read_paper_execution_evidence_bundle_retention_custody_inventory_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory_verification import (
    read_paper_execution_evidence_bundle_retention_custody_inventory_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation import (
    read_paper_execution_evidence_bundle_retention_custody_reconciliation_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation_verification import (
    read_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification import (
    read_paper_execution_evidence_bundle_retention_custody_certification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification_verification import (
    read_paper_execution_evidence_bundle_retention_custody_certification_verification_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation import (
    read_paper_execution_evidence_bundle_retention_custody_attestation_views,
)
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation_verification import (
    read_paper_execution_evidence_bundle_retention_custody_attestation_verification_views,
)
from strategy_validator.application.paper_execution_intent_selection import read_latest_paper_execution_intent_selection
from strategy_validator.application.paper_execution_order_status import read_paper_order_status_views
from strategy_validator.application.paper_execution_reconciliation import (
    build_paper_position_reconciliation_view,
    read_latest_paper_account_position_snapshot,
)
from strategy_validator.application.ui_paper_broker import build_ui_paper_broker_status_payload
from strategy_validator.application.ui_paper_tracking import discover_latest_paper_tracking
from strategy_validator.brokers.alpaca_paper import dry_run_paper_order
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent
from strategy_validator.contracts.paper_execution import (
    PaperExecutionCockpitPayload,
    PaperExecutionEvidenceBundleDriftView,
    PaperExecutionEvidenceBundleRotationView,
    PaperExecutionEvidenceBundleAttestationView,
    PaperExecutionEvidenceBundleAttestationVerificationView,
    PaperExecutionEvidenceBundleClosureView,
    PaperExecutionEvidenceBundleClosureVerificationView,
    PaperExecutionEvidenceBundleExportManifestView,
    PaperExecutionEvidenceBundleExportVerificationView,
    PaperExecutionEvidenceBundleRetentionReceiptView,
    PaperExecutionEvidenceBundleRetentionVerificationView,
    PaperExecutionEvidenceBundleRetentionSignoffView,
    PaperExecutionEvidenceBundleRetentionSignoffVerificationView,
    PaperExecutionEvidenceBundleRetentionHandoffView,
    PaperExecutionEvidenceBundleRetentionHandoffVerificationView,
    PaperExecutionEvidenceBundleRetentionHandoffAcceptanceView,
    PaperExecutionEvidenceBundleRetentionHandoffAcceptanceVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyRegisterView,
    PaperExecutionEvidenceBundleRetentionCustodyRegisterVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyReviewView,
    PaperExecutionEvidenceBundleRetentionCustodyReviewVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyRenewalView,
    PaperExecutionEvidenceBundleRetentionCustodyRenewalVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyScheduleView,
    PaperExecutionEvidenceBundleRetentionCustodyScheduleVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyNoticeView,
    PaperExecutionEvidenceBundleRetentionCustodyNoticeVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentView,
    PaperExecutionEvidenceBundleRetentionCustodyAcknowledgmentVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyCompletionView,
    PaperExecutionEvidenceBundleRetentionCustodyCompletionVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyCloseoutView,
    PaperExecutionEvidenceBundleRetentionCustodyCloseoutVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyArchiveView,
    PaperExecutionEvidenceBundleRetentionCustodyArchiveVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyRetrievalView,
    PaperExecutionEvidenceBundleRetentionCustodyRetrievalVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyReturnView,
    PaperExecutionEvidenceBundleRetentionCustodyReturnVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyRedepositView,
    PaperExecutionEvidenceBundleRetentionCustodyRedepositVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyInventoryView,
    PaperExecutionEvidenceBundleRetentionCustodyInventoryVerificationView,
    PaperExecutionEvidenceBundleRetentionCustodyReconciliationView,
    PaperExecutionEvidenceBundleRetentionCustodyReconciliationVerificationView,
    PaperExecutionEvidenceBundleRotationExecutionView,
    PaperExecutionFreshnessGate,
    PaperExecutionIntentPreview,
    PaperExecutionIntentSelectionArtifact,
    PaperExecutionJournalEntry,
    PaperExecutionOrderStatusView,
    PaperExecutionPositionReconciliationView,
    PaperExecutionSubmissionReceiptView,
    PaperExecutionSummary,
    PaperExecutionTimelineEntry,
    PaperExecutionTimelineSummary,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_SCHEMA = "ui_paper_execution_cockpit/v1"


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _strings(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if x not in (None, "")]
    if v in (None, ""):
        return []
    return [str(v)]



def _attestation_view_from_artifact(artifact) -> PaperExecutionEvidenceBundleAttestationView:
    return PaperExecutionEvidenceBundleAttestationView(
        tracking_id=artifact.tracking_id,
        artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
        artifact_sha256=artifact.artifact_sha256,
        generated_at_utc=artifact.generated_at_utc.isoformat(),
        attestation_status=artifact.attestation_status,
        trust_banner=artifact.trust_banner,
        attestation_mode=artifact.attestation_mode,
        signature_status=artifact.signature_status,
        signer_identity=artifact.signer_identity,
        source_bundle_sha256=artifact.source_bundle_sha256,
        source_bundle_status=artifact.source_bundle_status,
        source_verification_status=artifact.source_verification_status,
        source_drift_status=artifact.source_drift_status,
        statement_payload_sha256=artifact.statement_payload_sha256,
        blocker_count=len(artifact.blockers),
        warning_count=len(artifact.warnings),
        blockers=artifact.blockers,
        warnings=artifact.warnings,
    )

def _as_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _broker_status(repo_root: Path | None) -> tuple[dict[str, Any], str | None, list[str]]:
    path = paper_broker_status_artifact_path(repo_root)
    degraded: list[str] = []
    art = _safe_read_json(path)
    if art is not None:
        return art, str(path), degraded
    degraded.append("NO_PAPER_BROKER_STATUS_ARTIFACT")
    return build_ui_paper_broker_status_payload(), None, degraded


def _latest_signal(tracking: dict[str, Any]) -> dict[str, Any] | None:
    recent = tracking.get("signal_history_recent")
    if not isinstance(recent, list) or not recent:
        return None
    for row in reversed(recent):
        rec = _as_dict(row)
        summary = _as_dict(rec.get("summary"))
        if summary:
            return summary
    return None


def _infer_symbol(*, signal: dict[str, Any] | None, candidate: dict[str, Any]) -> tuple[str, list[str]]:
    warnings: list[str] = []
    meta = _as_dict(signal.get("signal_metadata")) if signal else {}
    for key in ("symbol", "ticker", "asset", "instrument"):
        raw = str(meta.get(key) or "").strip().upper()
        if raw:
            return raw, warnings
    sid = str(candidate.get("strategy_id") or "").lower()
    universe = str(candidate.get("data_plane_at_enrollment") or candidate.get("strategy_type") or "").lower()
    blob = f"{sid} {universe}"
    if "qqq" in blob:
        return "QQQ", warnings + ["SYMBOL_INFERRED_FROM_STRATEGY_ID"]
    if "spy" in blob or "sp500" in blob or "s&p" in blob:
        return "SPY", warnings + ["SYMBOL_INFERRED_FROM_STRATEGY_ID"]
    return "SPY", warnings + ["SYMBOL_NOT_DECLARED_DEFAULTED_TO_SPY"]


def _build_intent_preview(tracking: dict[str, Any]) -> PaperExecutionIntentPreview | None:
    manifest = _as_dict(tracking.get("manifest"))
    candidate = _as_dict(manifest.get("candidate"))
    tracking_id = str(tracking.get("tracking_id") or candidate.get("tracking_id") or "").strip()
    strategy_id = str(candidate.get("strategy_id") or "").strip()
    if not tracking_id:
        return None
    signal = _latest_signal(tracking)
    exposure = 0.0
    warnings: list[str] = []
    if signal is None:
        warnings.append("NO_DAILY_SIGNAL_SNAPSHOT_DEFAULTING_BUY_ONE_UNIT")
    else:
        try:
            exposure = float(signal.get("signal_exposure", 0.0) or 0.0)
        except (TypeError, ValueError):
            exposure = 0.0
            warnings.append("SIGNAL_EXPOSURE_INVALID_DEFAULTING_BUY_ONE_UNIT")
    side = "buy" if exposure >= 0 else "sell"
    qty = abs(exposure)
    if qty <= 0:
        qty = 1.0
        warnings.append("ZERO_SIGNAL_DEFAULTED_TO_ONE_UNIT")
    else:
        # This is only an execution-intent preview; keep unit size deliberately small.
        qty = max(0.0001, min(1.0, round(qty, 4)))
        warnings.append("PREVIEW_QTY_CLIPPED_TO_ONE_UNIT_MAX")
    symbol, sw = _infer_symbol(signal=signal, candidate=candidate)
    warnings.extend(sw)
    source = "latest_signal_snapshot" if signal else "tracking_manifest_default"
    return PaperExecutionIntentPreview(
        tracking_id=tracking_id,
        strategy_id=strategy_id or None,
        symbol=symbol,
        side=side,  # type: ignore[arg-type]
        qty=qty,
        source=source,
        rationale="Derived from latest paper tracking signal for dry-run validation only; not an order control.",
        confidence="LOW",
        warnings=sorted(set(warnings)),
    )



def _selected_artifact_to_preview(raw: dict[str, Any]) -> PaperExecutionIntentPreview | None:
    selected = _as_dict(raw.get("selected_intent"))
    if not selected:
        broker_intent = _as_dict(raw.get("broker_intent"))
        if not broker_intent:
            return None
        selected = {
            "schema_version": "paper_execution_intent_preview/v1",
            "tracking_id": broker_intent.get("tracking_id") or raw.get("tracking_id"),
            "strategy_id": raw.get("strategy_id"),
            "symbol": broker_intent.get("symbol"),
            "side": broker_intent.get("side"),
            "qty": broker_intent.get("qty"),
            "order_type": broker_intent.get("order_type", "market"),
            "time_in_force": broker_intent.get("time_in_force", "day"),
            "source": "selected_intent_artifact",
            "rationale": "Read from durable paper_execution_intent_selection artifact; dry-run preparation only.",
            "confidence": "MEDIUM",
            "warnings": ["SELECTED_INTENT_ARTIFACT"],
        }
    try:
        preview = PaperExecutionIntentPreview.model_validate(selected)
    except ValueError:
        return None
    warnings = sorted(set(preview.warnings + ["SELECTED_INTENT_ARTIFACT"]))
    return preview.model_copy(update={"source": "selected_intent_artifact", "confidence": "MEDIUM", "warnings": warnings})


def _selection_artifact(raw: dict[str, Any] | None) -> PaperExecutionIntentSelectionArtifact | None:
    if raw is None:
        return None
    try:
        return PaperExecutionIntentSelectionArtifact.model_validate({k: v for k, v in raw.items() if k != "artifact_path"})
    except ValueError:
        return None

def _dry_run(intent: PaperExecutionIntentPreview, env: dict[str, str]) -> dict[str, Any]:
    broker_intent = PaperBrokerOrderIntent(
        tracking_id=intent.tracking_id or "unknown",
        symbol=intent.symbol,
        side=intent.side,
        qty=float(intent.qty),
        order_type=intent.order_type,
        time_in_force=intent.time_in_force,
    )
    result = dry_run_paper_order(broker_intent, env)
    payload = result.model_dump(mode="json")
    payload["intent"] = intent.model_dump(mode="json")
    payload["submission_route"] = "CLI_ONLY"
    payload["browser_submission_available"] = False
    return payload


def _intent_selection_count(repo_root: Path | None) -> tuple[dict[str, Any] | None, int]:
    _, raw, count = read_latest_paper_execution_intent_selection(repo_root=repo_root)
    return raw, count


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


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

def _recommended_actions(
    *,
    broker_policy: str,
    tracking_present: bool,
    intent_count: int,
    selected_count: int,
    blocked_count: int,
    journal_count: int,
    replay_status: str,
    freshness_gate: PaperExecutionFreshnessGate | None = None,
    submission_receipt_count: int = 0,
    submission_guard_blocker_count: int = 0,
    latest_submission_guard_status: str | None = None,
    position_reconciliation: PaperExecutionPositionReconciliationView | None = None,
    order_statuses: list[PaperExecutionOrderStatusView] | None = None,
    timeline_summary: PaperExecutionTimelineSummary | None = None,
    latest_evidence_bundle: Any | None = None,
    latest_evidence_bundle_verification: Any | None = None,
    latest_evidence_bundle_drift: Any | None = None,
    latest_evidence_bundle_rotation: Any | None = None,
    latest_evidence_bundle_rotation_execution: Any | None = None,
    latest_evidence_bundle_attestation: Any | None = None,
    latest_evidence_bundle_attestation_verification: Any | None = None,
    latest_evidence_bundle_closure: Any | None = None,
    latest_evidence_bundle_closure_verification: Any | None = None,
    latest_evidence_bundle_export_manifest: Any | None = None,
    latest_evidence_bundle_export_verification: Any | None = None,
    latest_evidence_bundle_retention_receipt: Any | None = None,
    latest_evidence_bundle_retention_verification: Any | None = None,
    latest_evidence_bundle_retention_signoff: Any | None = None,
    latest_evidence_bundle_retention_signoff_verification: Any | None = None,
    latest_evidence_bundle_retention_handoff: Any | None = None,
    latest_evidence_bundle_retention_handoff_verification: Any | None = None,
    latest_evidence_bundle_retention_handoff_acceptance: Any | None = None,
    latest_evidence_bundle_retention_handoff_acceptance_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_register: Any | None = None,
    latest_evidence_bundle_retention_custody_register_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_seal: Any | None = None,
    latest_evidence_bundle_retention_custody_seal_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_audit: Any | None = None,
    latest_evidence_bundle_retention_custody_audit_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_continuity: Any | None = None,
    latest_evidence_bundle_retention_custody_continuity_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_review: Any | None = None,
    latest_evidence_bundle_retention_custody_review_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_renewal: Any | None = None,
    latest_evidence_bundle_retention_custody_renewal_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_schedule: Any | None = None,
    latest_evidence_bundle_retention_custody_schedule_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_notice: Any | None = None,
    latest_evidence_bundle_retention_custody_notice_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_acknowledgment: Any | None = None,
    latest_evidence_bundle_retention_custody_acknowledgment_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_completion: Any | None = None,
    latest_evidence_bundle_retention_custody_completion_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_closeout: Any | None = None,
    latest_evidence_bundle_retention_custody_closeout_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_archive: Any | None = None,
    latest_evidence_bundle_retention_custody_archive_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_retrieval: Any | None = None,
    latest_evidence_bundle_retention_custody_retrieval_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_return: Any | None = None,
    latest_evidence_bundle_retention_custody_return_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_redeposit: Any | None = None,
    latest_evidence_bundle_retention_custody_redeposit_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_inventory: Any | None = None,
    latest_evidence_bundle_retention_custody_inventory_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_reconciliation: Any | None = None,
    latest_evidence_bundle_retention_custody_reconciliation_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_certification: Any | None = None,
    latest_evidence_bundle_retention_custody_certification_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_attestation: Any | None = None,
    latest_evidence_bundle_retention_custody_attestation_verification: Any | None = None,
) -> list[str]:
    actions: list[str] = []
    if broker_policy != "PAPER_READY":
        actions.append("Resolve paper broker policy blockers or missing Alpaca paper keys before CLI dry-run/order evidence.")
    if not tracking_present:
        actions.append("Enroll at least one strategy into paper tracking before generating paper execution previews.")
    if tracking_present and intent_count == 0:
        actions.append("Append a daily paper signal snapshot so the cockpit can derive a candidate execution intent.")
    if tracking_present and selected_count == 0:
        actions.append("Select a paper execution intent with strategy-validator-paper-broker select-intent before durable dry-run evidence.")
    if selected_count and replay_status == "NO_DRY_RUN":
        actions.append("Replay the selected intent with strategy-validator-paper-broker dry-run-selected-intent to bind dry-run evidence to the selection SHA.")
    if replay_status == "MISMATCHED":
        actions.append("Latest linked dry-run evidence does not match the current selected intent SHA; rerun dry-run-selected-intent.")
    if freshness_gate is not None:
        if freshness_gate.status == "STALE":
            actions.append("Refresh stale paper execution evidence: reselect the intent if needed, rerun dry-run-selected-intent, and regenerate broker policy/status evidence.")
        elif freshness_gate.status == "REPLAY_REQUIRED":
            actions.append("Freshness gate requires replay: run strategy-validator-paper-broker dry-run-selected-intent for the current selected intent.")
        elif freshness_gate.status == "MISSING_EVIDENCE":
            actions.append("Freshness gate is missing required paper execution evidence; select an intent and materialize linked dry-run evidence before trusting the cockpit.")
    if blocked_count:
        actions.append("Inspect dry-run blockers; browser routes intentionally cannot bypass broker policy.")
    if submission_receipt_count and submission_guard_blocker_count:
        actions.append("Review guarded paper submission receipt blockers before trusting the latest paper submission artifact.")
    if latest_submission_guard_status == "PASS":
        actions.append("Latest paper submission receipt is guard-passed; keep reviewing CLI-only receipts before any operational decision.")
    if latest_submission_guard_status == "PASS" and not order_statuses:
        actions.append("Refresh broker order status with strategy-validator-paper-broker refresh-order-status after guarded paper submission.")
    if order_statuses and order_statuses[0].status not in {"filled", "partially_filled"}:
        actions.append("Latest paper order status is not filled; refresh order status before expecting position reconciliation.")
    if timeline_summary is not None:
        if timeline_summary.sequence_status == "PARTIAL":
            actions.append("Review the paper execution timeline and complete missing evidence stages before trusting the paper execution loop.")
        elif timeline_summary.sequence_status == "BLOCKED":
            actions.append("Resolve paper execution timeline blockers before treating CLI evidence as trusted.")
        elif timeline_summary.sequence_status == "COMPLETE" and latest_evidence_bundle is None:
            actions.append("Seal the completed paper execution timeline with strategy-validator-paper-broker seal-evidence-bundle for digest-anchored review evidence.")
    if latest_evidence_bundle is not None:
        if getattr(latest_evidence_bundle, "trust_banner", "TRUST_RESTRICTED") != "TRUSTED":
            actions.append("Review the latest paper execution evidence bundle warnings/blockers before treating the timeline as trusted.")
        if latest_evidence_bundle_verification is None:
            actions.append("Verify the sealed paper execution evidence bundle with strategy-validator-paper-broker verify-evidence-bundle before treating it as independently trusted.")
    if latest_evidence_bundle_verification is not None:
        if getattr(latest_evidence_bundle_verification, "verification_status", "FAIL") != "PASS":
            actions.append("Latest paper execution evidence bundle verification failed; re-seal or repair mismatched source artifacts before relying on the bundle.")
    if latest_evidence_bundle is not None and latest_evidence_bundle_drift is None:
        actions.append("Check sealed-bundle drift with strategy-validator-paper-broker check-evidence-bundle-drift after verifying the bundle.")
    if latest_evidence_bundle_drift is not None:
        if getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") == "DRIFTED":
            actions.append("Latest verified paper execution bundle is drifted from the current timeline; re-seal and re-verify the evidence bundle.")
        elif getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") in {"NO_BUNDLE", "NO_TIMELINE"}:
            actions.append("Bundle drift check cannot establish current trust; complete the timeline and seal a bundle before relying on paper execution evidence.")
    if latest_evidence_bundle_rotation is not None:
        rotation_status = getattr(latest_evidence_bundle_rotation, "rotation_status", "UNKNOWN")
        if rotation_status == "REQUIRED":
            actions.append("Run strategy-validator-paper-broker run-evidence-bundle-rotation to execute the safe re-seal / verify / drift-check workflow.")
        elif rotation_status == "RECOMMENDED":
            actions.append("Run strategy-validator-paper-broker run-evidence-bundle-rotation to follow the latest paper evidence-bundle rotation recommendation.")
        elif rotation_status == "BLOCKED":
            actions.append("Resolve paper evidence-bundle rotation blockers before resealing the timeline.")
    if latest_evidence_bundle_rotation_execution is not None:
        execution_status = getattr(latest_evidence_bundle_rotation_execution, "rotation_execution_status", "UNKNOWN")
        if execution_status == "FAILED":
            actions.append("Latest paper evidence-bundle rotation execution failed; inspect the execution manifest and repair failed steps before trusting the bundle.")
        elif execution_status == "BLOCKED":
            actions.append("Latest paper evidence-bundle rotation execution is blocked; complete timeline or recommendation prerequisites before rerunning.")
        elif execution_status == "SKIPPED":
            actions.append("Latest paper evidence-bundle rotation execution was skipped because rotation was not needed; continue drift monitoring.")
    if latest_evidence_bundle_attestation is None:
        if latest_evidence_bundle_verification is not None and getattr(latest_evidence_bundle_verification, "verification_status", "UNKNOWN") == "PASS" and latest_evidence_bundle_drift is not None and getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") == "IN_SYNC":
            actions.append("Write a keyless local paper evidence-bundle attestation with strategy-validator-paper-broker attest-evidence-bundle.")
    else:
        attestation_status = getattr(latest_evidence_bundle_attestation, "attestation_status", "UNKNOWN")
        if attestation_status == "BLOCKED":
            actions.append("Paper evidence-bundle attestation is blocked; verify bundle and resolve drift before attesting.")
        elif getattr(latest_evidence_bundle_attestation, "blocker_count", 0):
            actions.append("Review paper evidence-bundle attestation blockers before trusting attested paper execution evidence.")
        if latest_evidence_bundle_attestation_verification is None and attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"}:
            actions.append("Verify the paper evidence-bundle attestation with strategy-validator-paper-broker verify-evidence-bundle-attestation before treating the attestation artifact as tamper-checked.")
    if latest_evidence_bundle_attestation_verification is not None:
        attestation_verification_status = getattr(latest_evidence_bundle_attestation_verification, "verification_status", "UNKNOWN")
        if attestation_verification_status != "PASS":
            actions.append("Latest paper evidence-bundle attestation verification failed; inspect attestation hash, payload, and referenced artifact links before relying on it.")
        elif latest_evidence_bundle_closure is None:
            actions.append("Write a final paper evidence-bundle closure packet with strategy-validator-paper-broker close-evidence-bundle.")
    if latest_evidence_bundle_closure is not None:
        closure_status = getattr(latest_evidence_bundle_closure, "closure_status", "UNKNOWN")
        if closure_status == "BLOCKED":
            actions.append("Paper evidence-bundle closure is blocked; resolve closure blockers before relying on the paper evidence chain.")
        elif closure_status == "READY_RESTRICTED":
            actions.append("Paper evidence-bundle closure is restricted; review closure warnings before archiving the paper evidence chain.")
        elif latest_evidence_bundle_closure_verification is None:
            actions.append("Verify the paper evidence-bundle closure packet with strategy-validator-paper-broker verify-evidence-bundle-closure before archiving the evidence chain.")
    if latest_evidence_bundle_closure_verification is not None:
        closure_verification_status = getattr(latest_evidence_bundle_closure_verification, "verification_status", "UNKNOWN")
        if closure_verification_status != "PASS":
            actions.append("Latest paper evidence-bundle closure verification failed; inspect closure hash and referenced artifact links before archiving the chain.")
        elif latest_evidence_bundle_export_manifest is None:
            actions.append("Write a paper evidence-chain export handoff manifest with strategy-validator-paper-broker export-evidence-bundle-chain before external retention.")
    if latest_evidence_bundle_export_manifest is not None:
        export_status = getattr(latest_evidence_bundle_export_manifest, "export_status", "UNKNOWN")
        if export_status == "BLOCKED":
            actions.append("Paper evidence-chain export handoff manifest is blocked; repair missing or mismatched retained artifacts before external retention.")
        elif export_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain export handoff manifest is restricted; review warnings before external retention.")
        elif latest_evidence_bundle_export_verification is None:
            actions.append("Verify the paper evidence-chain export handoff manifest with strategy-validator-paper-broker verify-evidence-bundle-export before external retention.")
    if latest_evidence_bundle_export_verification is not None:
        export_verification_status = getattr(latest_evidence_bundle_export_verification, "verification_status", "UNKNOWN")
        if export_verification_status != "PASS":
            actions.append("Latest paper evidence-chain export verification failed; inspect export manifest hash, index hash, and retained artifact entry digests before external retention.")
        elif latest_evidence_bundle_retention_receipt is None:
            actions.append("Write a paper evidence-chain retention receipt with strategy-validator-paper-broker receipt-evidence-bundle-retention before external retention.")
    if latest_evidence_bundle_retention_receipt is not None:
        retention_status = getattr(latest_evidence_bundle_retention_receipt, "retention_status", "UNKNOWN")
        if retention_status == "BLOCKED":
            actions.append("Paper evidence-chain retention receipt is blocked; inspect missing or mismatched retained files before external retention.")
        elif retention_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain retention receipt is restricted; review warnings before external retention.")
        elif latest_evidence_bundle_retention_verification is None:
            actions.append("Verify the paper evidence-chain retention receipt with strategy-validator-paper-broker verify-evidence-bundle-retention before external retention.")
    if latest_evidence_bundle_retention_verification is not None:
        retention_verification_status = getattr(latest_evidence_bundle_retention_verification, "verification_status", "UNKNOWN")
        if retention_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention verification failed; inspect retention receipt hash, index hash, file digests, and sizes before external retention.")
        elif latest_evidence_bundle_retention_signoff is None:
            actions.append("Write a paper evidence-chain retention signoff with strategy-validator-paper-broker signoff-evidence-bundle-retention before external retention handoff.")
    if latest_evidence_bundle_retention_signoff is not None:
        signoff_status = getattr(latest_evidence_bundle_retention_signoff, "signoff_status", "UNKNOWN")
        if signoff_status == "BLOCKED":
            actions.append("Paper evidence-chain retention signoff is blocked; inspect signoff blockers before external retention handoff.")
        elif signoff_status == "SIGNED_OFF_RESTRICTED":
            actions.append("Paper evidence-chain retention signoff is restricted; review warnings before external retention handoff.")
        elif latest_evidence_bundle_retention_signoff_verification is None:
            actions.append("Verify the paper evidence-chain retention signoff with strategy-validator-paper-broker verify-evidence-bundle-retention-signoff before external retention handoff.")
    if latest_evidence_bundle_retention_signoff_verification is not None:
        signoff_verification_status = getattr(latest_evidence_bundle_retention_signoff_verification, "verification_status", "UNKNOWN")
        if signoff_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention signoff verification failed; inspect signoff artifact hash, statement hash, and source retention verification digest before external retention handoff.")
        elif latest_evidence_bundle_retention_handoff is None:
            actions.append("Write a final paper evidence-chain retention handoff capsule with strategy-validator-paper-broker handoff-evidence-bundle-retention before custody acceptance.")
    if latest_evidence_bundle_retention_handoff is not None:
        handoff_status = getattr(latest_evidence_bundle_retention_handoff, "handoff_status", "UNKNOWN")
        if handoff_status == "BLOCKED":
            actions.append("Paper evidence-chain retention handoff is blocked; inspect handoff blockers before custody acceptance.")
        elif handoff_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain retention handoff is restricted; review warnings before custody acceptance.")
        elif latest_evidence_bundle_retention_handoff_verification is None:
            actions.append("Verify the paper evidence-chain retention handoff with strategy-validator-paper-broker verify-evidence-bundle-retention-handoff before custody acceptance.")
    if latest_evidence_bundle_retention_handoff_verification is not None:
        handoff_verification_status = getattr(latest_evidence_bundle_retention_handoff_verification, "verification_status", "UNKNOWN")
        if handoff_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention handoff verification failed; inspect handoff artifact hash, statement hash, and source signoff verification digest before custody acceptance.")
        elif latest_evidence_bundle_retention_handoff_acceptance is None:
            actions.append("Accept the verified paper evidence-chain retention handoff with strategy-validator-paper-broker accept-evidence-bundle-retention-handoff before custody registration.")
    if latest_evidence_bundle_retention_handoff_acceptance is not None:
        acceptance_status = getattr(latest_evidence_bundle_retention_handoff_acceptance, "acceptance_status", "UNKNOWN")
        if acceptance_status == "BLOCKED":
            actions.append("Paper evidence-chain retention handoff acceptance is blocked; inspect acceptance blockers before custody registration.")
        elif acceptance_status == "ACCEPTED_RESTRICTED":
            actions.append("Paper evidence-chain retention handoff acceptance is restricted; review warnings before custody registration.")
        elif latest_evidence_bundle_retention_handoff_acceptance_verification is None:
            actions.append("Verify the paper evidence-chain retention handoff acceptance with strategy-validator-paper-broker verify-evidence-bundle-retention-handoff-acceptance before custody registration.")
    if latest_evidence_bundle_retention_handoff_acceptance_verification is not None:
        acceptance_verification_status = getattr(latest_evidence_bundle_retention_handoff_acceptance_verification, "verification_status", "UNKNOWN")
        if acceptance_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention handoff acceptance verification failed; inspect acceptance artifact hash, statement hash, and source handoff verification digest before custody registration.")
        elif latest_evidence_bundle_retention_custody_register is None:
            actions.append("Register the accepted paper evidence-chain retention custody with strategy-validator-paper-broker register-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_register is not None:
        register_status = getattr(latest_evidence_bundle_retention_custody_register, "register_status", "UNKNOWN")
        if register_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody register is blocked; inspect register blockers before final custody verification.")
        elif register_status == "REGISTERED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody register is restricted; review warnings before final custody verification.")
        elif latest_evidence_bundle_retention_custody_register_verification is None:
            actions.append("Verify the paper evidence-chain retention custody register with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-register.")
    if latest_evidence_bundle_retention_custody_register_verification is not None:
        custody_register_verification_status = getattr(latest_evidence_bundle_retention_custody_register_verification, "verification_status", "UNKNOWN")
        if custody_register_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody register verification failed; inspect register hash, statement hash, and source acceptance verification digest.")
        elif latest_evidence_bundle_retention_custody_seal is None:
            actions.append("Seal the verified paper evidence-chain retention custody with strategy-validator-paper-broker seal-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_seal is not None:
        seal_status = getattr(latest_evidence_bundle_retention_custody_seal, "seal_status", "UNKNOWN")
        if seal_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody seal is blocked; inspect seal blockers before final verification.")
        elif seal_status == "SEALED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody seal is restricted; review warnings before relying on the sealed custody state.")
        elif latest_evidence_bundle_retention_custody_seal_verification is None:
            actions.append("Verify the paper evidence-chain retention custody seal with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-seal.")
    if latest_evidence_bundle_retention_custody_seal_verification is not None:
        seal_verification_status = getattr(latest_evidence_bundle_retention_custody_seal_verification, "verification_status", "UNKNOWN")
        if seal_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody seal verification failed; inspect seal hash, statement hash, and source custody-register verification digest.")
        elif latest_evidence_bundle_retention_custody_audit is None:
            actions.append("Audit the verified paper evidence-chain retention custody seal with strategy-validator-paper-broker audit-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_audit is not None:
        audit_status = getattr(latest_evidence_bundle_retention_custody_audit, "audit_status", "UNKNOWN")
        if audit_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody audit is blocked; inspect audit blockers before relying on retained custody evidence.")
        elif audit_status == "AUDITED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody audit is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_audit_verification is None:
            actions.append("Verify the paper evidence-chain retention custody audit with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-audit.")
    if latest_evidence_bundle_retention_custody_audit_verification is not None:
        audit_verification_status = getattr(latest_evidence_bundle_retention_custody_audit_verification, "verification_status", "UNKNOWN")
        if audit_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody audit verification failed; inspect audit hash, statement hash, and source custody-seal verification digest.")
        elif latest_evidence_bundle_retention_custody_continuity is None:
            actions.append("Attest paper evidence-chain retention custody continuity with strategy-validator-paper-broker attest-evidence-bundle-retention-custody-continuity.")
    if latest_evidence_bundle_retention_custody_continuity is not None:
        continuity_status = getattr(latest_evidence_bundle_retention_custody_continuity, "continuity_status", "UNKNOWN")
        if continuity_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody continuity is blocked; inspect continuity blockers before verification.")
        elif continuity_status == "CONTINUITY_RESTRICTED":
            actions.append("Paper evidence-chain retention custody continuity is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_continuity_verification is None:
            actions.append("Verify the paper evidence-chain retention custody continuity attestation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-continuity.")
    if latest_evidence_bundle_retention_custody_continuity_verification is not None:
        continuity_verification_status = getattr(latest_evidence_bundle_retention_custody_continuity_verification, "verification_status", "UNKNOWN")
        if continuity_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody continuity verification failed; inspect continuity hash, statement hash, and source custody-audit verification digest.")
        elif latest_evidence_bundle_retention_custody_review is None:
            actions.append("Review the paper evidence-chain retention custody continuity with strategy-validator-paper-broker review-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_review is not None:
        review_status = getattr(latest_evidence_bundle_retention_custody_review, "review_status", "UNKNOWN")
        if review_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody review is blocked; inspect review blockers before verification.")
        elif review_status == "REVIEW_RESTRICTED":
            actions.append("Paper evidence-chain retention custody review is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_review_verification is None:
            actions.append("Verify the paper evidence-chain retention custody review with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-review.")
    if latest_evidence_bundle_retention_custody_review_verification is not None:
        review_verification_status = getattr(latest_evidence_bundle_retention_custody_review_verification, "verification_status", "UNKNOWN")
        if review_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody review verification failed; inspect review hash, statement hash, and source custody-continuity verification digest.")
        elif latest_evidence_bundle_retention_custody_renewal is None:
            actions.append("Renew the verified paper evidence-chain retention custody with strategy-validator-paper-broker renew-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_renewal is not None:
        renewal_status = getattr(latest_evidence_bundle_retention_custody_renewal, "renewal_status", "UNKNOWN")
        if renewal_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal is blocked; inspect renewal blockers before scheduling the next renewal.")
        elif renewal_status == "RENEWAL_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal is restricted; review warnings before scheduling the next renewal.")
        elif latest_evidence_bundle_retention_custody_renewal_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_renewal_verification is not None:
        renewal_verification_status = getattr(latest_evidence_bundle_retention_custody_renewal_verification, "verification_status", "UNKNOWN")
        if renewal_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal verification failed; inspect renewal hash, statement hash, and source custody-review verification digest.")
        elif latest_evidence_bundle_retention_custody_schedule is None:
            actions.append("Schedule the next paper evidence-chain retention custody renewal with strategy-validator-paper-broker schedule-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_schedule is not None:
        schedule_status = getattr(latest_evidence_bundle_retention_custody_schedule, "schedule_status", "UNKNOWN")
        if schedule_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal schedule is blocked; inspect schedule blockers before relying on the due date.")
        elif schedule_status == "SCHEDULE_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal schedule is restricted; review warnings before relying on the due date.")
        elif latest_evidence_bundle_retention_custody_schedule_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal schedule with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-schedule.")
    if latest_evidence_bundle_retention_custody_schedule_verification is not None:
        schedule_verification_status = getattr(latest_evidence_bundle_retention_custody_schedule_verification, "verification_status", "UNKNOWN")
        if schedule_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal schedule verification failed; inspect schedule hash, statement hash, and source custody-renewal verification digest.")
        elif latest_evidence_bundle_retention_custody_notice is None:
            actions.append("Generate the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker notice-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_notice is not None:
        notice_status = getattr(latest_evidence_bundle_retention_custody_notice, "notice_status", "UNKNOWN")
        if notice_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal notice is blocked; inspect notice blockers before verification.")
        elif notice_status == "NOTICE_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal notice is restricted; inspect warnings before relying on renewal scheduling notice.")
        elif latest_evidence_bundle_retention_custody_notice_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-notice.")
    if latest_evidence_bundle_retention_custody_notice_verification is not None:
        notice_verification_status = getattr(latest_evidence_bundle_retention_custody_notice_verification, "verification_status", "UNKNOWN")
        if notice_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal notice verification failed; inspect notice hash, statement hash, and source schedule verification digest.")
        elif latest_evidence_bundle_retention_custody_acknowledgment is None:
            actions.append("Acknowledge the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker acknowledge-evidence-bundle-retention-custody-notice.")
    if latest_evidence_bundle_retention_custody_acknowledgment is not None:
        acknowledgment_status = getattr(latest_evidence_bundle_retention_custody_acknowledgment, "acknowledgment_status", "UNKNOWN")
        if acknowledgment_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal notice acknowledgment is blocked; inspect acknowledgment blockers before verification.")
        elif acknowledgment_status == "ACKNOWLEDGED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal notice acknowledgment is restricted; inspect warnings before treating the notice as operator-accepted.")
        elif latest_evidence_bundle_retention_custody_acknowledgment_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal notice acknowledgment with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-acknowledgment.")
    if latest_evidence_bundle_retention_custody_acknowledgment_verification is not None:
        acknowledgment_verification_status = getattr(latest_evidence_bundle_retention_custody_acknowledgment_verification, "verification_status", "UNKNOWN")
        if acknowledgment_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal notice acknowledgment verification failed; inspect acknowledgment hash, statement hash, and source notice verification digest.")
        elif latest_evidence_bundle_retention_custody_completion is None:
            actions.append("Complete the paper evidence-chain retention custody renewal with strategy-validator-paper-broker complete-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_completion is not None:
        completion_status = getattr(latest_evidence_bundle_retention_custody_completion, "completion_status", "UNKNOWN")
        if completion_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal completion is blocked; inspect completion blockers before verification.")
        elif completion_status == "COMPLETED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal completion is restricted; inspect warnings before closing out the renewal cycle.")
        elif latest_evidence_bundle_retention_custody_completion_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal completion with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-completion.")
    if latest_evidence_bundle_retention_custody_completion_verification is not None:
        completion_verification_status = getattr(latest_evidence_bundle_retention_custody_completion_verification, "verification_status", "UNKNOWN")
        if completion_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal completion verification failed; inspect completion hash, statement hash, and source acknowledgment verification digest.")
        elif latest_evidence_bundle_retention_custody_closeout is None:
            actions.append("Close out the verified paper evidence-chain retention custody renewal cycle with strategy-validator-paper-broker closeout-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_closeout is not None:
        closeout_status = getattr(latest_evidence_bundle_retention_custody_closeout, "closeout_status", "UNKNOWN")
        if closeout_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal closeout is blocked; inspect closeout blockers before verification.")
        elif closeout_status == "CLOSED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal closeout is restricted; inspect warnings before treating the renewal cycle as closed.")
        elif latest_evidence_bundle_retention_custody_closeout_verification is None:
            actions.append("Verify the paper evidence-chain retention custody closeout with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-closeout.")
    if latest_evidence_bundle_retention_custody_closeout_verification is not None:
        closeout_verification_status = getattr(latest_evidence_bundle_retention_custody_closeout_verification, "verification_status", "UNKNOWN")
        if closeout_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody closeout verification failed; inspect closeout hash, statement hash, and source completion verification digest.")
        elif latest_evidence_bundle_retention_custody_archive is None:
            actions.append("Archive the verified paper evidence-chain retention custody closeout with strategy-validator-paper-broker archive-evidence-bundle-retention-custody-closeout.")
    if latest_evidence_bundle_retention_custody_archive is not None:
        archive_status = getattr(latest_evidence_bundle_retention_custody_archive, "archive_status", "UNKNOWN")
        if archive_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody archive is blocked; inspect archive blockers before verification.")
        elif archive_status == "ARCHIVED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody archive is restricted; inspect warnings before retrieval.")
        elif latest_evidence_bundle_retention_custody_archive_verification is None:
            actions.append("Verify the paper evidence-chain retention custody archive with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-archive.")
    if latest_evidence_bundle_retention_custody_archive_verification is not None:
        archive_verification_status = getattr(latest_evidence_bundle_retention_custody_archive_verification, "verification_status", "UNKNOWN")
        if archive_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody archive verification failed; inspect archive hash, statement hash, and source closeout verification digest.")
        elif latest_evidence_bundle_retention_custody_retrieval is None:
            actions.append("Retrieve the verified archived paper evidence-chain retention custody bundle with strategy-validator-paper-broker retrieve-evidence-bundle-retention-custody-archive.")
    if latest_evidence_bundle_retention_custody_retrieval is not None:
        retrieval_status = getattr(latest_evidence_bundle_retention_custody_retrieval, "retrieval_status", "UNKNOWN")
        if retrieval_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody retrieval is blocked; inspect retrieval blockers before verification.")
        elif retrieval_status == "RETRIEVED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody retrieval is restricted; inspect warnings before relying on retrieval evidence.")
        elif latest_evidence_bundle_retention_custody_retrieval_verification is None:
            actions.append("Verify the paper evidence-chain retention custody retrieval with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-retrieval.")
    if latest_evidence_bundle_retention_custody_retrieval_verification is not None:
        retrieval_verification_status = getattr(latest_evidence_bundle_retention_custody_retrieval_verification, "verification_status", "UNKNOWN")
        if retrieval_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody retrieval verification failed; inspect retrieval hash, statement hash, and source archive verification digest.")
        elif latest_evidence_bundle_retention_custody_return is None:
            actions.append("Return the verified retrieved paper evidence-chain retention custody bundle with strategy-validator-paper-broker return-evidence-bundle-retention-custody-retrieval.")
    if latest_evidence_bundle_retention_custody_return is not None:
        return_status = getattr(latest_evidence_bundle_retention_custody_return, "return_status", "UNKNOWN")
        if return_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody return is blocked; inspect return blockers before verification.")
        elif return_status == "RETURNED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody return is restricted; inspect warnings before relying on return evidence.")
        elif latest_evidence_bundle_retention_custody_return_verification is None:
            actions.append("Verify the paper evidence-chain retention custody return with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-return.")
    if latest_evidence_bundle_retention_custody_return_verification is not None:
        return_verification_status = getattr(latest_evidence_bundle_retention_custody_return_verification, "verification_status", "UNKNOWN")
        if return_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody return verification failed; inspect return hash, statement hash, and source retrieval verification digest.")
        elif latest_evidence_bundle_retention_custody_redeposit is None:
            actions.append("Redeposit the verified returned paper evidence-chain retention custody bundle with strategy-validator-paper-broker redeposit-evidence-bundle-retention-custody-return.")
    if latest_evidence_bundle_retention_custody_redeposit is not None:
        redeposit_status = getattr(latest_evidence_bundle_retention_custody_redeposit, "redeposit_status", "UNKNOWN")
        if redeposit_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody redeposit is blocked; inspect redeposit blockers before verification.")
        elif redeposit_status == "REDEPOSITED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody redeposit is restricted; inspect warnings before relying on redeposit evidence.")
        elif latest_evidence_bundle_retention_custody_redeposit_verification is None:
            actions.append("Verify the paper evidence-chain retention custody redeposit with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-redeposit.")
    if latest_evidence_bundle_retention_custody_redeposit_verification is not None:
        redeposit_verification_status = getattr(latest_evidence_bundle_retention_custody_redeposit_verification, "verification_status", "UNKNOWN")
        if redeposit_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody redeposit verification failed; inspect redeposit hash, statement hash, and source return verification digest.")
        elif latest_evidence_bundle_retention_custody_inventory is None:
            actions.append("Inventory the verified redeposited paper evidence-chain retention custody bundle with strategy-validator-paper-broker inventory-evidence-bundle-retention-custody-redeposit.")
    if latest_evidence_bundle_retention_custody_inventory is not None:
        inventory_status = getattr(latest_evidence_bundle_retention_custody_inventory, "inventory_status", "UNKNOWN")
        if inventory_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody inventory is blocked; inspect inventory blockers before verification.")
        elif inventory_status == "INVENTORIED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody inventory is restricted; inspect warnings before relying on inventory evidence.")
        elif latest_evidence_bundle_retention_custody_inventory_verification is None:
            actions.append("Verify the paper evidence-chain retention custody inventory with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-inventory.")
    if latest_evidence_bundle_retention_custody_inventory_verification is not None:
        inventory_verification_status = getattr(latest_evidence_bundle_retention_custody_inventory_verification, "verification_status", "UNKNOWN")
        if inventory_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody inventory verification failed; inspect inventory hash, statement hash, and source redeposit verification digest.")
        elif latest_evidence_bundle_retention_custody_reconciliation is None:
            actions.append("Reconcile the verified paper evidence-chain retention custody inventory with strategy-validator-paper-broker reconcile-evidence-bundle-retention-custody-inventory.")
    if latest_evidence_bundle_retention_custody_reconciliation is not None:
        reconciliation_status = getattr(latest_evidence_bundle_retention_custody_reconciliation, "reconciliation_status", "UNKNOWN")
        if reconciliation_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody reconciliation is blocked; inspect reconciliation blockers before verification.")
        elif reconciliation_status == "RECONCILED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody reconciliation is restricted; inspect warnings before relying on reconciliation evidence.")
        elif latest_evidence_bundle_retention_custody_reconciliation_verification is None:
            actions.append("Verify the paper evidence-chain retention custody reconciliation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-reconciliation.")
    if latest_evidence_bundle_retention_custody_reconciliation_verification is not None:
        reconciliation_verification_status = getattr(latest_evidence_bundle_retention_custody_reconciliation_verification, "verification_status", "UNKNOWN")
        if reconciliation_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody reconciliation verification failed; inspect reconciliation hash, statement hash, and source inventory verification digest.")
        elif latest_evidence_bundle_retention_custody_certification is None:
            actions.append("Certify the verified paper evidence-chain retention custody reconciliation with strategy-validator-paper-broker certify-evidence-bundle-retention-custody-reconciliation.")
    if latest_evidence_bundle_retention_custody_certification is not None:
        certification_status = getattr(latest_evidence_bundle_retention_custody_certification, "certification_status", "UNKNOWN")
        if certification_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody certification is blocked; inspect certification blockers before verification.")
        elif certification_status == "CERTIFIED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody certification is restricted; inspect warnings before relying on certification evidence.")
        elif latest_evidence_bundle_retention_custody_certification_verification is None:
            actions.append("Verify the paper evidence-chain retention custody certification with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-certification.")
    if latest_evidence_bundle_retention_custody_certification_verification is not None:
        certification_verification_status = getattr(latest_evidence_bundle_retention_custody_certification_verification, "verification_status", "UNKNOWN")
        if certification_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody certification verification failed; inspect certification hash, statement hash, and source reconciliation verification digest.")
        elif latest_evidence_bundle_retention_custody_attestation is None:
            actions.append("Attest the verified paper evidence-chain retention custody certification with strategy-validator-paper-broker attest-evidence-bundle-retention-custody-certification.")
    if latest_evidence_bundle_retention_custody_attestation is not None:
        attestation_status = getattr(latest_evidence_bundle_retention_custody_attestation, "attestation_status", "UNKNOWN")
        if attestation_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody attestation is blocked; inspect attestation blockers before verification.")
        elif attestation_status == "ATTESTED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody attestation is restricted; inspect warnings before relying on attestation evidence.")
        elif latest_evidence_bundle_retention_custody_attestation_verification is None:
            actions.append("Verify the paper evidence-chain retention custody attestation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-attestation.")
    if latest_evidence_bundle_retention_custody_attestation_verification is not None:
        attestation_verification_status = getattr(latest_evidence_bundle_retention_custody_attestation_verification, "verification_status", "UNKNOWN")
        if attestation_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody attestation verification failed; inspect attestation hash, statement hash, and source certification verification digest.")
    if position_reconciliation is not None:
        if position_reconciliation.status == "NO_POSITION_SNAPSHOT":
            actions.append("Capture a paper account/position snapshot with strategy-validator-paper-broker snapshot-account-positions after guarded paper submissions.")
        elif position_reconciliation.status == "PENDING_FILL":
            actions.append("Latest paper submission is not filled yet; refresh account/position snapshot after broker fill status changes.")
        elif position_reconciliation.status == "MISMATCHED":
            actions.append("Investigate broker-state mismatch: latest guarded paper receipt does not reconcile with the position snapshot.")
        elif position_reconciliation.reconciliation_blocker_count:
            actions.append("Review paper account/position reconciliation blockers before trusting paper broker state.")
    if journal_count == 0:
        actions.append("Use strategy-validator-paper-broker dry-run-order or submit-paper-order on a trusted host to materialize paper broker evidence.")
    if not actions:
        actions.append("Paper execution cockpit is populated; continue using CLI-only order submission and review journal evidence.")
    return actions


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
    evidence_bundles = read_paper_execution_evidence_bundle_views(repo_root=repo_root)
    latest_evidence_bundle = evidence_bundles[0] if evidence_bundles else None
    evidence_bundle_verifications = read_paper_execution_evidence_bundle_verification_views(repo_root=repo_root)
    latest_evidence_bundle_verification = evidence_bundle_verifications[0] if evidence_bundle_verifications else None
    evidence_bundle_drifts = read_paper_execution_evidence_bundle_drift_views(repo_root=repo_root)
    latest_evidence_bundle_drift = evidence_bundle_drifts[0] if evidence_bundle_drifts else None
    if latest_evidence_bundle is not None:
        current_drift = build_paper_execution_evidence_bundle_drift_artifact(
            current_timeline=execution_timeline,
            current_timeline_summary=execution_timeline_summary,
            bundle_artifact_path=Path(latest_evidence_bundle.artifact_path),
            bundle_raw=_safe_read_json(Path(latest_evidence_bundle.artifact_path)),
            generated_at_utc=now,
        )
        latest_evidence_bundle_drift = PaperExecutionEvidenceBundleDriftView(
            tracking_id=current_drift.tracking_id,
            artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
            artifact_sha256=current_drift.artifact_sha256,
            generated_at_utc=current_drift.generated_at_utc.isoformat(),
            drift_status=current_drift.drift_status,
            trust_banner=current_drift.trust_banner,
            source_bundle_artifact_path=current_drift.source_bundle_artifact_path,
            source_bundle_sha256=current_drift.source_bundle_sha256,
            source_bundle_generated_at_utc=current_drift.source_bundle_generated_at_utc,
            current_timeline_sequence_status=current_drift.current_timeline_sequence_status,
            current_timeline_event_count=current_drift.current_timeline_event_count,
            bundled_timeline_event_count=current_drift.bundled_timeline_event_count,
            current_source_artifact_count=current_drift.current_source_artifact_count,
            bundled_source_artifact_count=current_drift.bundled_source_artifact_count,
            current_timeline_fingerprint=current_drift.current_timeline_fingerprint,
            bundled_timeline_fingerprint=current_drift.bundled_timeline_fingerprint,
            new_source_artifact_count=len(current_drift.new_source_artifacts),
            removed_source_artifact_count=len(current_drift.removed_source_artifacts),
            changed_stage_count=current_drift.changed_stage_count,
            blockers=current_drift.blockers,
            warnings=current_drift.warnings,
        )
        evidence_bundle_drifts = [latest_evidence_bundle_drift, *evidence_bundle_drifts]
    evidence_bundle_rotations = read_paper_execution_evidence_bundle_rotation_views(repo_root=repo_root)
    current_rotation = build_paper_execution_evidence_bundle_rotation_artifact(
        timeline_summary=execution_timeline_summary,
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        generated_at_utc=now,
    )
    latest_evidence_bundle_rotation = PaperExecutionEvidenceBundleRotationView(
        tracking_id=current_rotation.tracking_id,
        artifact_path="CURRENT_PROJECTION_NOT_PERSISTED",
        artifact_sha256=current_rotation.artifact_sha256,
        generated_at_utc=current_rotation.generated_at_utc.isoformat(),
        rotation_status=current_rotation.rotation_status,
        trust_banner=current_rotation.trust_banner,
        source_bundle_sha256=current_rotation.source_bundle_sha256,
        source_bundle_status=current_rotation.source_bundle_status,
        source_verification_status=current_rotation.source_verification_status,
        source_drift_status=current_rotation.source_drift_status,
        timeline_sequence_status=current_rotation.timeline_sequence_status,
        timeline_event_count=current_rotation.timeline_event_count,
        rotation_reason_codes=current_rotation.rotation_reason_codes,
        recommended_operator_sequence=current_rotation.recommended_operator_sequence,
        one_command_sequence_hint=current_rotation.one_command_sequence_hint,
        blockers=current_rotation.blockers,
        warnings=current_rotation.warnings,
    )
    evidence_bundle_rotations = [latest_evidence_bundle_rotation, *evidence_bundle_rotations]
    evidence_bundle_rotation_executions = read_paper_execution_evidence_bundle_rotation_execution_views(repo_root=repo_root)
    latest_evidence_bundle_rotation_execution = evidence_bundle_rotation_executions[0] if evidence_bundle_rotation_executions else None
    persisted_evidence_bundle_attestations = read_paper_execution_evidence_bundle_attestation_views(repo_root=repo_root)
    current_attestation = build_paper_execution_evidence_bundle_attestation_artifact(
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        generated_at_utc=now,
    )
    current_evidence_bundle_attestation = _attestation_view_from_artifact(current_attestation)
    latest_evidence_bundle_attestation = persisted_evidence_bundle_attestations[0] if persisted_evidence_bundle_attestations else current_evidence_bundle_attestation
    evidence_bundle_attestations = [latest_evidence_bundle_attestation, current_evidence_bundle_attestation, *persisted_evidence_bundle_attestations[1:]]
    evidence_bundle_attestation_verifications = read_paper_execution_evidence_bundle_attestation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_attestation_verification = evidence_bundle_attestation_verifications[0] if evidence_bundle_attestation_verifications else None
    persisted_evidence_bundle_closures = read_paper_execution_evidence_bundle_closure_views(repo_root=repo_root)
    current_closure = build_paper_execution_evidence_bundle_closure_artifact(
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        latest_evidence_bundle_attestation=latest_evidence_bundle_attestation,
        latest_evidence_bundle_attestation_verification=latest_evidence_bundle_attestation_verification,
        generated_at_utc=now,
    )
    current_evidence_bundle_closure = _closure_view_from_artifact(current_closure, artifact_path="CURRENT_PROJECTION_NOT_PERSISTED")
    latest_evidence_bundle_closure = persisted_evidence_bundle_closures[0] if persisted_evidence_bundle_closures else current_evidence_bundle_closure
    evidence_bundle_closures = [latest_evidence_bundle_closure, current_evidence_bundle_closure, *persisted_evidence_bundle_closures[1:]]
    evidence_bundle_closure_verifications = read_paper_execution_evidence_bundle_closure_verification_views(repo_root=repo_root)
    latest_evidence_bundle_closure_verification = evidence_bundle_closure_verifications[0] if evidence_bundle_closure_verifications else None
    evidence_bundle_export_manifests = read_paper_execution_evidence_bundle_export_manifest_views(repo_root=repo_root)
    latest_evidence_bundle_export_manifest = evidence_bundle_export_manifests[0] if evidence_bundle_export_manifests else None
    evidence_bundle_export_verifications = read_paper_execution_evidence_bundle_export_verification_views(repo_root=repo_root)
    latest_evidence_bundle_export_verification = evidence_bundle_export_verifications[0] if evidence_bundle_export_verifications else None
    evidence_bundle_retention_receipts = read_paper_execution_evidence_bundle_retention_receipt_views(repo_root=repo_root)
    latest_evidence_bundle_retention_receipt = evidence_bundle_retention_receipts[0] if evidence_bundle_retention_receipts else None
    evidence_bundle_retention_verifications = read_paper_execution_evidence_bundle_retention_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_verification = evidence_bundle_retention_verifications[0] if evidence_bundle_retention_verifications else None
    evidence_bundle_retention_signoffs = read_paper_execution_evidence_bundle_retention_signoff_views(repo_root=repo_root)
    latest_evidence_bundle_retention_signoff = evidence_bundle_retention_signoffs[0] if evidence_bundle_retention_signoffs else None
    evidence_bundle_retention_signoff_verifications = read_paper_execution_evidence_bundle_retention_signoff_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_signoff_verification = evidence_bundle_retention_signoff_verifications[0] if evidence_bundle_retention_signoff_verifications else None
    evidence_bundle_retention_handoffs = read_paper_execution_evidence_bundle_retention_handoff_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff = evidence_bundle_retention_handoffs[0] if evidence_bundle_retention_handoffs else None
    evidence_bundle_retention_handoff_verifications = read_paper_execution_evidence_bundle_retention_handoff_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_verification = evidence_bundle_retention_handoff_verifications[0] if evidence_bundle_retention_handoff_verifications else None
    evidence_bundle_retention_handoff_acceptances = read_paper_execution_evidence_bundle_retention_handoff_acceptance_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_acceptance = evidence_bundle_retention_handoff_acceptances[0] if evidence_bundle_retention_handoff_acceptances else None
    evidence_bundle_retention_handoff_acceptance_verifications = read_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_handoff_acceptance_verification = evidence_bundle_retention_handoff_acceptance_verifications[0] if evidence_bundle_retention_handoff_acceptance_verifications else None
    evidence_bundle_retention_custody_registers = read_paper_execution_evidence_bundle_retention_custody_register_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_register = evidence_bundle_retention_custody_registers[0] if evidence_bundle_retention_custody_registers else None
    evidence_bundle_retention_custody_register_verifications = read_paper_execution_evidence_bundle_retention_custody_register_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_register_verification = evidence_bundle_retention_custody_register_verifications[0] if evidence_bundle_retention_custody_register_verifications else None
    evidence_bundle_retention_custody_seals = read_paper_execution_evidence_bundle_retention_custody_seal_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_seal = evidence_bundle_retention_custody_seals[0] if evidence_bundle_retention_custody_seals else None
    evidence_bundle_retention_custody_seal_verifications = read_paper_execution_evidence_bundle_retention_custody_seal_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_seal_verification = evidence_bundle_retention_custody_seal_verifications[0] if evidence_bundle_retention_custody_seal_verifications else None
    evidence_bundle_retention_custody_audits = read_paper_execution_evidence_bundle_retention_custody_audit_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_audit = evidence_bundle_retention_custody_audits[0] if evidence_bundle_retention_custody_audits else None
    evidence_bundle_retention_custody_audit_verifications = read_paper_execution_evidence_bundle_retention_custody_audit_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_audit_verification = evidence_bundle_retention_custody_audit_verifications[0] if evidence_bundle_retention_custody_audit_verifications else None
    evidence_bundle_retention_custody_continuities = read_paper_execution_evidence_bundle_retention_custody_continuity_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_continuity = evidence_bundle_retention_custody_continuities[0] if evidence_bundle_retention_custody_continuities else None
    evidence_bundle_retention_custody_continuity_verifications = read_paper_execution_evidence_bundle_retention_custody_continuity_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_continuity_verification = evidence_bundle_retention_custody_continuity_verifications[0] if evidence_bundle_retention_custody_continuity_verifications else None
    evidence_bundle_retention_custody_reviews = read_paper_execution_evidence_bundle_retention_custody_review_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_review = evidence_bundle_retention_custody_reviews[0] if evidence_bundle_retention_custody_reviews else None
    evidence_bundle_retention_custody_review_verifications = read_paper_execution_evidence_bundle_retention_custody_review_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_review_verification = evidence_bundle_retention_custody_review_verifications[0] if evidence_bundle_retention_custody_review_verifications else None
    evidence_bundle_retention_custody_renewals = read_paper_execution_evidence_bundle_retention_custody_renewal_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_renewal = evidence_bundle_retention_custody_renewals[0] if evidence_bundle_retention_custody_renewals else None
    evidence_bundle_retention_custody_renewal_verifications = read_paper_execution_evidence_bundle_retention_custody_renewal_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_renewal_verification = evidence_bundle_retention_custody_renewal_verifications[0] if evidence_bundle_retention_custody_renewal_verifications else None
    evidence_bundle_retention_custody_schedules = read_paper_execution_evidence_bundle_retention_custody_schedule_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_schedule = evidence_bundle_retention_custody_schedules[0] if evidence_bundle_retention_custody_schedules else None
    evidence_bundle_retention_custody_schedule_verifications = read_paper_execution_evidence_bundle_retention_custody_schedule_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_schedule_verification = evidence_bundle_retention_custody_schedule_verifications[0] if evidence_bundle_retention_custody_schedule_verifications else None
    evidence_bundle_retention_custody_notices = read_paper_execution_evidence_bundle_retention_custody_notice_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_notice = evidence_bundle_retention_custody_notices[0] if evidence_bundle_retention_custody_notices else None
    evidence_bundle_retention_custody_notice_verifications = read_paper_execution_evidence_bundle_retention_custody_notice_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_notice_verification = evidence_bundle_retention_custody_notice_verifications[0] if evidence_bundle_retention_custody_notice_verifications else None
    evidence_bundle_retention_custody_acknowledgments = read_paper_execution_evidence_bundle_retention_custody_acknowledgment_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_acknowledgment = evidence_bundle_retention_custody_acknowledgments[0] if evidence_bundle_retention_custody_acknowledgments else None
    evidence_bundle_retention_custody_acknowledgment_verifications = read_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_acknowledgment_verification = evidence_bundle_retention_custody_acknowledgment_verifications[0] if evidence_bundle_retention_custody_acknowledgment_verifications else None
    evidence_bundle_retention_custody_completions = read_paper_execution_evidence_bundle_retention_custody_completion_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_completion = evidence_bundle_retention_custody_completions[0] if evidence_bundle_retention_custody_completions else None
    evidence_bundle_retention_custody_completion_verifications = read_paper_execution_evidence_bundle_retention_custody_completion_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_completion_verification = evidence_bundle_retention_custody_completion_verifications[0] if evidence_bundle_retention_custody_completion_verifications else None
    evidence_bundle_retention_custody_closeouts = read_paper_execution_evidence_bundle_retention_custody_closeout_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_closeout = evidence_bundle_retention_custody_closeouts[0] if evidence_bundle_retention_custody_closeouts else None
    evidence_bundle_retention_custody_closeout_verifications = read_paper_execution_evidence_bundle_retention_custody_closeout_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_closeout_verification = evidence_bundle_retention_custody_closeout_verifications[0] if evidence_bundle_retention_custody_closeout_verifications else None
    evidence_bundle_retention_custody_archives = read_paper_execution_evidence_bundle_retention_custody_archive_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_archive = evidence_bundle_retention_custody_archives[0] if evidence_bundle_retention_custody_archives else None
    evidence_bundle_retention_custody_archive_verifications = read_paper_execution_evidence_bundle_retention_custody_archive_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_archive_verification = evidence_bundle_retention_custody_archive_verifications[0] if evidence_bundle_retention_custody_archive_verifications else None
    evidence_bundle_retention_custody_retrievals = read_paper_execution_evidence_bundle_retention_custody_retrieval_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_retrieval = evidence_bundle_retention_custody_retrievals[0] if evidence_bundle_retention_custody_retrievals else None
    evidence_bundle_retention_custody_retrieval_verifications = read_paper_execution_evidence_bundle_retention_custody_retrieval_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_retrieval_verification = evidence_bundle_retention_custody_retrieval_verifications[0] if evidence_bundle_retention_custody_retrieval_verifications else None
    evidence_bundle_retention_custody_returns = read_paper_execution_evidence_bundle_retention_custody_return_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_return = evidence_bundle_retention_custody_returns[0] if evidence_bundle_retention_custody_returns else None
    evidence_bundle_retention_custody_return_verifications = read_paper_execution_evidence_bundle_retention_custody_return_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_return_verification = evidence_bundle_retention_custody_return_verifications[0] if evidence_bundle_retention_custody_return_verifications else None
    evidence_bundle_retention_custody_redeposits = read_paper_execution_evidence_bundle_retention_custody_redeposit_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_redeposit = evidence_bundle_retention_custody_redeposits[0] if evidence_bundle_retention_custody_redeposits else None
    evidence_bundle_retention_custody_redeposit_verifications = read_paper_execution_evidence_bundle_retention_custody_redeposit_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_redeposit_verification = evidence_bundle_retention_custody_redeposit_verifications[0] if evidence_bundle_retention_custody_redeposit_verifications else None
    evidence_bundle_retention_custody_inventories = read_paper_execution_evidence_bundle_retention_custody_inventory_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_inventory = evidence_bundle_retention_custody_inventories[0] if evidence_bundle_retention_custody_inventories else None
    evidence_bundle_retention_custody_inventory_verifications = read_paper_execution_evidence_bundle_retention_custody_inventory_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_inventory_verification = evidence_bundle_retention_custody_inventory_verifications[0] if evidence_bundle_retention_custody_inventory_verifications else None
    evidence_bundle_retention_custody_reconciliations = read_paper_execution_evidence_bundle_retention_custody_reconciliation_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_reconciliation = evidence_bundle_retention_custody_reconciliations[0] if evidence_bundle_retention_custody_reconciliations else None
    evidence_bundle_retention_custody_reconciliation_verifications = read_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_reconciliation_verification = evidence_bundle_retention_custody_reconciliation_verifications[0] if evidence_bundle_retention_custody_reconciliation_verifications else None
    evidence_bundle_retention_custody_certifications = read_paper_execution_evidence_bundle_retention_custody_certification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_certification = evidence_bundle_retention_custody_certifications[0] if evidence_bundle_retention_custody_certifications else None
    evidence_bundle_retention_custody_certification_verifications = read_paper_execution_evidence_bundle_retention_custody_certification_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_certification_verification = evidence_bundle_retention_custody_certification_verifications[0] if evidence_bundle_retention_custody_certification_verifications else None
    evidence_bundle_retention_custody_attestations = read_paper_execution_evidence_bundle_retention_custody_attestation_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_attestation = evidence_bundle_retention_custody_attestations[0] if evidence_bundle_retention_custody_attestations else None
    evidence_bundle_retention_custody_attestation_verifications = read_paper_execution_evidence_bundle_retention_custody_attestation_verification_views(repo_root=repo_root)
    latest_evidence_bundle_retention_custody_attestation_verification = evidence_bundle_retention_custody_attestation_verifications[0] if evidence_bundle_retention_custody_attestation_verifications else None
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
        latest_tracking_id=str((latest_tracking or {}).get("tracking_id") or "") or None,
        latest_strategy_id=str(candidate.get("strategy_id") or "") or None,
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
        evidence_bundle_count=len(evidence_bundles),
        latest_evidence_bundle_at_utc=latest_evidence_bundle.generated_at_utc if latest_evidence_bundle else None,
        latest_evidence_bundle_trust_banner=latest_evidence_bundle.trust_banner if latest_evidence_bundle else None,
        latest_evidence_bundle_status=latest_evidence_bundle.bundle_status if latest_evidence_bundle else None,
        latest_evidence_bundle_sha256=latest_evidence_bundle.bundle_sha256 if latest_evidence_bundle else None,
        evidence_bundle_blocker_count=sum(len(row.blockers) for row in evidence_bundles),
        evidence_bundle_verification_count=len(evidence_bundle_verifications),
        latest_evidence_bundle_verification_at_utc=latest_evidence_bundle_verification.generated_at_utc if latest_evidence_bundle_verification else None,
        latest_evidence_bundle_verification_status=latest_evidence_bundle_verification.verification_status if latest_evidence_bundle_verification else None,
        latest_evidence_bundle_verification_trust_banner=latest_evidence_bundle_verification.trust_banner if latest_evidence_bundle_verification else None,
        latest_evidence_bundle_verification_sha256=latest_evidence_bundle_verification.artifact_sha256 if latest_evidence_bundle_verification else None,
        evidence_bundle_verification_blocker_count=sum(len(row.blockers) for row in evidence_bundle_verifications),
        evidence_bundle_drift_count=len(evidence_bundle_drifts),
        latest_evidence_bundle_drift_at_utc=latest_evidence_bundle_drift.generated_at_utc if latest_evidence_bundle_drift else None,
        latest_evidence_bundle_drift_status=latest_evidence_bundle_drift.drift_status if latest_evidence_bundle_drift else None,
        latest_evidence_bundle_drift_trust_banner=latest_evidence_bundle_drift.trust_banner if latest_evidence_bundle_drift else None,
        latest_evidence_bundle_drift_sha256=latest_evidence_bundle_drift.artifact_sha256 if latest_evidence_bundle_drift else None,
        evidence_bundle_drift_blocker_count=sum(len(row.blockers) for row in evidence_bundle_drifts),
        evidence_bundle_drift_new_source_count=sum(row.new_source_artifact_count for row in evidence_bundle_drifts),
        evidence_bundle_drift_removed_source_count=sum(row.removed_source_artifact_count for row in evidence_bundle_drifts),
        evidence_bundle_rotation_count=len(evidence_bundle_rotations),
        latest_evidence_bundle_rotation_at_utc=latest_evidence_bundle_rotation.generated_at_utc if latest_evidence_bundle_rotation else None,
        latest_evidence_bundle_rotation_status=latest_evidence_bundle_rotation.rotation_status if latest_evidence_bundle_rotation else None,
        latest_evidence_bundle_rotation_trust_banner=latest_evidence_bundle_rotation.trust_banner if latest_evidence_bundle_rotation else None,
        latest_evidence_bundle_rotation_sha256=latest_evidence_bundle_rotation.artifact_sha256 if latest_evidence_bundle_rotation else None,
        evidence_bundle_rotation_blocker_count=sum(len(row.blockers) for row in evidence_bundle_rotations),
        evidence_bundle_rotation_execution_count=len(evidence_bundle_rotation_executions),
        latest_evidence_bundle_rotation_execution_at_utc=latest_evidence_bundle_rotation_execution.generated_at_utc if latest_evidence_bundle_rotation_execution else None,
        latest_evidence_bundle_rotation_execution_status=latest_evidence_bundle_rotation_execution.rotation_execution_status if latest_evidence_bundle_rotation_execution else None,
        latest_evidence_bundle_rotation_execution_trust_banner=latest_evidence_bundle_rotation_execution.trust_banner if latest_evidence_bundle_rotation_execution else None,
        latest_evidence_bundle_rotation_execution_sha256=latest_evidence_bundle_rotation_execution.artifact_sha256 if latest_evidence_bundle_rotation_execution else None,
        evidence_bundle_rotation_execution_blocker_count=sum(len(row.blockers) for row in evidence_bundle_rotation_executions),
        evidence_bundle_attestation_count=len(evidence_bundle_attestations),
        latest_evidence_bundle_attestation_at_utc=latest_evidence_bundle_attestation.generated_at_utc if latest_evidence_bundle_attestation else None,
        latest_evidence_bundle_attestation_status=latest_evidence_bundle_attestation.attestation_status if latest_evidence_bundle_attestation else None,
        latest_evidence_bundle_attestation_trust_banner=latest_evidence_bundle_attestation.trust_banner if latest_evidence_bundle_attestation else None,
        latest_evidence_bundle_attestation_sha256=latest_evidence_bundle_attestation.artifact_sha256 if latest_evidence_bundle_attestation else None,
        evidence_bundle_attestation_blocker_count=sum(row.blocker_count for row in evidence_bundle_attestations),
        evidence_bundle_attestation_verification_count=len(evidence_bundle_attestation_verifications),
        latest_evidence_bundle_attestation_verification_at_utc=latest_evidence_bundle_attestation_verification.generated_at_utc if latest_evidence_bundle_attestation_verification else None,
        latest_evidence_bundle_attestation_verification_status=latest_evidence_bundle_attestation_verification.verification_status if latest_evidence_bundle_attestation_verification else None,
        latest_evidence_bundle_attestation_verification_trust_banner=latest_evidence_bundle_attestation_verification.trust_banner if latest_evidence_bundle_attestation_verification else None,
        latest_evidence_bundle_attestation_verification_sha256=latest_evidence_bundle_attestation_verification.artifact_sha256 if latest_evidence_bundle_attestation_verification else None,
        evidence_bundle_attestation_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_attestation_verifications),
        evidence_bundle_closure_count=len(evidence_bundle_closures),
        latest_evidence_bundle_closure_at_utc=latest_evidence_bundle_closure.generated_at_utc if latest_evidence_bundle_closure else None,
        latest_evidence_bundle_closure_status=latest_evidence_bundle_closure.closure_status if latest_evidence_bundle_closure else None,
        latest_evidence_bundle_closure_trust_banner=latest_evidence_bundle_closure.trust_banner if latest_evidence_bundle_closure else None,
        latest_evidence_bundle_closure_sha256=latest_evidence_bundle_closure.artifact_sha256 if latest_evidence_bundle_closure else None,
        evidence_bundle_closure_blocker_count=sum(row.blocker_count for row in evidence_bundle_closures),
        evidence_bundle_closure_verification_count=len(evidence_bundle_closure_verifications),
        latest_evidence_bundle_closure_verification_at_utc=latest_evidence_bundle_closure_verification.generated_at_utc if latest_evidence_bundle_closure_verification else None,
        latest_evidence_bundle_closure_verification_status=latest_evidence_bundle_closure_verification.verification_status if latest_evidence_bundle_closure_verification else None,
        latest_evidence_bundle_closure_verification_trust_banner=latest_evidence_bundle_closure_verification.trust_banner if latest_evidence_bundle_closure_verification else None,
        latest_evidence_bundle_closure_verification_sha256=latest_evidence_bundle_closure_verification.artifact_sha256 if latest_evidence_bundle_closure_verification else None,
        evidence_bundle_closure_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_closure_verifications),
        evidence_bundle_export_manifest_count=len(evidence_bundle_export_manifests),
        latest_evidence_bundle_export_manifest_at_utc=latest_evidence_bundle_export_manifest.generated_at_utc if latest_evidence_bundle_export_manifest else None,
        latest_evidence_bundle_export_manifest_status=latest_evidence_bundle_export_manifest.export_status if latest_evidence_bundle_export_manifest else None,
        latest_evidence_bundle_export_manifest_trust_banner=latest_evidence_bundle_export_manifest.trust_banner if latest_evidence_bundle_export_manifest else None,
        latest_evidence_bundle_export_manifest_sha256=latest_evidence_bundle_export_manifest.artifact_sha256 if latest_evidence_bundle_export_manifest else None,
        evidence_bundle_export_manifest_blocker_count=sum(row.blocker_count for row in evidence_bundle_export_manifests),
        evidence_bundle_export_verification_count=len(evidence_bundle_export_verifications),
        latest_evidence_bundle_export_verification_at_utc=latest_evidence_bundle_export_verification.generated_at_utc if latest_evidence_bundle_export_verification else None,
        latest_evidence_bundle_export_verification_status=latest_evidence_bundle_export_verification.verification_status if latest_evidence_bundle_export_verification else None,
        latest_evidence_bundle_export_verification_trust_banner=latest_evidence_bundle_export_verification.trust_banner if latest_evidence_bundle_export_verification else None,
        latest_evidence_bundle_export_verification_sha256=latest_evidence_bundle_export_verification.artifact_sha256 if latest_evidence_bundle_export_verification else None,
        evidence_bundle_export_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_export_verifications),
        evidence_bundle_retention_receipt_count=len(evidence_bundle_retention_receipts),
        latest_evidence_bundle_retention_receipt_at_utc=latest_evidence_bundle_retention_receipt.generated_at_utc if latest_evidence_bundle_retention_receipt else None,
        latest_evidence_bundle_retention_receipt_status=latest_evidence_bundle_retention_receipt.retention_status if latest_evidence_bundle_retention_receipt else None,
        latest_evidence_bundle_retention_receipt_trust_banner=latest_evidence_bundle_retention_receipt.trust_banner if latest_evidence_bundle_retention_receipt else None,
        latest_evidence_bundle_retention_receipt_sha256=latest_evidence_bundle_retention_receipt.artifact_sha256 if latest_evidence_bundle_retention_receipt else None,
        evidence_bundle_retention_receipt_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_receipts),
        evidence_bundle_retention_verification_count=len(evidence_bundle_retention_verifications),
        latest_evidence_bundle_retention_verification_at_utc=latest_evidence_bundle_retention_verification.generated_at_utc if latest_evidence_bundle_retention_verification else None,
        latest_evidence_bundle_retention_verification_status=latest_evidence_bundle_retention_verification.verification_status if latest_evidence_bundle_retention_verification else None,
        latest_evidence_bundle_retention_verification_trust_banner=latest_evidence_bundle_retention_verification.trust_banner if latest_evidence_bundle_retention_verification else None,
        latest_evidence_bundle_retention_verification_sha256=latest_evidence_bundle_retention_verification.artifact_sha256 if latest_evidence_bundle_retention_verification else None,
        evidence_bundle_retention_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_verifications),
        evidence_bundle_retention_signoff_count=len(evidence_bundle_retention_signoffs),
        latest_evidence_bundle_retention_signoff_at_utc=latest_evidence_bundle_retention_signoff.generated_at_utc if latest_evidence_bundle_retention_signoff else None,
        latest_evidence_bundle_retention_signoff_status=latest_evidence_bundle_retention_signoff.signoff_status if latest_evidence_bundle_retention_signoff else None,
        latest_evidence_bundle_retention_signoff_trust_banner=latest_evidence_bundle_retention_signoff.trust_banner if latest_evidence_bundle_retention_signoff else None,
        latest_evidence_bundle_retention_signoff_sha256=latest_evidence_bundle_retention_signoff.artifact_sha256 if latest_evidence_bundle_retention_signoff else None,
        evidence_bundle_retention_signoff_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_signoffs),
        evidence_bundle_retention_signoff_verification_count=len(evidence_bundle_retention_signoff_verifications),
        latest_evidence_bundle_retention_signoff_verification_at_utc=latest_evidence_bundle_retention_signoff_verification.generated_at_utc if latest_evidence_bundle_retention_signoff_verification else None,
        latest_evidence_bundle_retention_signoff_verification_status=latest_evidence_bundle_retention_signoff_verification.verification_status if latest_evidence_bundle_retention_signoff_verification else None,
        latest_evidence_bundle_retention_signoff_verification_trust_banner=latest_evidence_bundle_retention_signoff_verification.trust_banner if latest_evidence_bundle_retention_signoff_verification else None,
        latest_evidence_bundle_retention_signoff_verification_sha256=latest_evidence_bundle_retention_signoff_verification.artifact_sha256 if latest_evidence_bundle_retention_signoff_verification else None,
        evidence_bundle_retention_signoff_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_signoff_verifications),
        evidence_bundle_retention_handoff_count=len(evidence_bundle_retention_handoffs),
        latest_evidence_bundle_retention_handoff_at_utc=latest_evidence_bundle_retention_handoff.generated_at_utc if latest_evidence_bundle_retention_handoff else None,
        latest_evidence_bundle_retention_handoff_status=latest_evidence_bundle_retention_handoff.handoff_status if latest_evidence_bundle_retention_handoff else None,
        latest_evidence_bundle_retention_handoff_trust_banner=latest_evidence_bundle_retention_handoff.trust_banner if latest_evidence_bundle_retention_handoff else None,
        latest_evidence_bundle_retention_handoff_sha256=latest_evidence_bundle_retention_handoff.artifact_sha256 if latest_evidence_bundle_retention_handoff else None,
        evidence_bundle_retention_handoff_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_handoffs),
        evidence_bundle_retention_handoff_verification_count=len(evidence_bundle_retention_handoff_verifications),
        latest_evidence_bundle_retention_handoff_verification_at_utc=latest_evidence_bundle_retention_handoff_verification.generated_at_utc if latest_evidence_bundle_retention_handoff_verification else None,
        latest_evidence_bundle_retention_handoff_verification_status=latest_evidence_bundle_retention_handoff_verification.verification_status if latest_evidence_bundle_retention_handoff_verification else None,
        latest_evidence_bundle_retention_handoff_verification_trust_banner=latest_evidence_bundle_retention_handoff_verification.trust_banner if latest_evidence_bundle_retention_handoff_verification else None,
        latest_evidence_bundle_retention_handoff_verification_sha256=latest_evidence_bundle_retention_handoff_verification.artifact_sha256 if latest_evidence_bundle_retention_handoff_verification else None,
        evidence_bundle_retention_handoff_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_handoff_verifications),
        evidence_bundle_retention_handoff_acceptance_count=len(evidence_bundle_retention_handoff_acceptances),
        latest_evidence_bundle_retention_handoff_acceptance_at_utc=latest_evidence_bundle_retention_handoff_acceptance.generated_at_utc if latest_evidence_bundle_retention_handoff_acceptance else None,
        latest_evidence_bundle_retention_handoff_acceptance_status=latest_evidence_bundle_retention_handoff_acceptance.acceptance_status if latest_evidence_bundle_retention_handoff_acceptance else None,
        latest_evidence_bundle_retention_handoff_acceptance_trust_banner=latest_evidence_bundle_retention_handoff_acceptance.trust_banner if latest_evidence_bundle_retention_handoff_acceptance else None,
        latest_evidence_bundle_retention_handoff_acceptance_sha256=latest_evidence_bundle_retention_handoff_acceptance.artifact_sha256 if latest_evidence_bundle_retention_handoff_acceptance else None,
        evidence_bundle_retention_handoff_acceptance_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_handoff_acceptances),
        evidence_bundle_retention_handoff_acceptance_verification_count=len(evidence_bundle_retention_handoff_acceptance_verifications),
        latest_evidence_bundle_retention_handoff_acceptance_verification_at_utc=latest_evidence_bundle_retention_handoff_acceptance_verification.generated_at_utc if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
        latest_evidence_bundle_retention_handoff_acceptance_verification_status=latest_evidence_bundle_retention_handoff_acceptance_verification.verification_status if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
        latest_evidence_bundle_retention_handoff_acceptance_verification_trust_banner=latest_evidence_bundle_retention_handoff_acceptance_verification.trust_banner if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
        latest_evidence_bundle_retention_handoff_acceptance_verification_sha256=latest_evidence_bundle_retention_handoff_acceptance_verification.artifact_sha256 if latest_evidence_bundle_retention_handoff_acceptance_verification else None,
        evidence_bundle_retention_handoff_acceptance_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_handoff_acceptance_verifications),
        evidence_bundle_retention_custody_register_count=len(evidence_bundle_retention_custody_registers),
        latest_evidence_bundle_retention_custody_register_at_utc=latest_evidence_bundle_retention_custody_register.generated_at_utc if latest_evidence_bundle_retention_custody_register else None,
        latest_evidence_bundle_retention_custody_register_status=latest_evidence_bundle_retention_custody_register.register_status if latest_evidence_bundle_retention_custody_register else None,
        latest_evidence_bundle_retention_custody_register_trust_banner=latest_evidence_bundle_retention_custody_register.trust_banner if latest_evidence_bundle_retention_custody_register else None,
        latest_evidence_bundle_retention_custody_register_sha256=latest_evidence_bundle_retention_custody_register.artifact_sha256 if latest_evidence_bundle_retention_custody_register else None,
        evidence_bundle_retention_custody_register_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_registers),
        evidence_bundle_retention_custody_register_verification_count=len(evidence_bundle_retention_custody_register_verifications),
        latest_evidence_bundle_retention_custody_register_verification_at_utc=latest_evidence_bundle_retention_custody_register_verification.generated_at_utc if latest_evidence_bundle_retention_custody_register_verification else None,
        latest_evidence_bundle_retention_custody_register_verification_status=latest_evidence_bundle_retention_custody_register_verification.verification_status if latest_evidence_bundle_retention_custody_register_verification else None,
        latest_evidence_bundle_retention_custody_register_verification_trust_banner=latest_evidence_bundle_retention_custody_register_verification.trust_banner if latest_evidence_bundle_retention_custody_register_verification else None,
        latest_evidence_bundle_retention_custody_register_verification_sha256=latest_evidence_bundle_retention_custody_register_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_register_verification else None,
        evidence_bundle_retention_custody_register_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_register_verifications),
        evidence_bundle_retention_custody_seal_count=len(evidence_bundle_retention_custody_seals),
        latest_evidence_bundle_retention_custody_seal_at_utc=latest_evidence_bundle_retention_custody_seal.generated_at_utc if latest_evidence_bundle_retention_custody_seal else None,
        latest_evidence_bundle_retention_custody_seal_status=latest_evidence_bundle_retention_custody_seal.seal_status if latest_evidence_bundle_retention_custody_seal else None,
        latest_evidence_bundle_retention_custody_seal_trust_banner=latest_evidence_bundle_retention_custody_seal.trust_banner if latest_evidence_bundle_retention_custody_seal else None,
        latest_evidence_bundle_retention_custody_seal_sha256=latest_evidence_bundle_retention_custody_seal.artifact_sha256 if latest_evidence_bundle_retention_custody_seal else None,
        evidence_bundle_retention_custody_seal_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_seals),
        evidence_bundle_retention_custody_seal_verification_count=len(evidence_bundle_retention_custody_seal_verifications),
        latest_evidence_bundle_retention_custody_seal_verification_at_utc=latest_evidence_bundle_retention_custody_seal_verification.generated_at_utc if latest_evidence_bundle_retention_custody_seal_verification else None,
        latest_evidence_bundle_retention_custody_seal_verification_status=latest_evidence_bundle_retention_custody_seal_verification.verification_status if latest_evidence_bundle_retention_custody_seal_verification else None,
        latest_evidence_bundle_retention_custody_seal_verification_trust_banner=latest_evidence_bundle_retention_custody_seal_verification.trust_banner if latest_evidence_bundle_retention_custody_seal_verification else None,
        latest_evidence_bundle_retention_custody_seal_verification_sha256=latest_evidence_bundle_retention_custody_seal_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_seal_verification else None,
        evidence_bundle_retention_custody_seal_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_seal_verifications),
        evidence_bundle_retention_custody_audit_count=len(evidence_bundle_retention_custody_audits),
        latest_evidence_bundle_retention_custody_audit_at_utc=latest_evidence_bundle_retention_custody_audit.generated_at_utc if latest_evidence_bundle_retention_custody_audit else None,
        latest_evidence_bundle_retention_custody_audit_status=latest_evidence_bundle_retention_custody_audit.audit_status if latest_evidence_bundle_retention_custody_audit else None,
        latest_evidence_bundle_retention_custody_audit_trust_banner=latest_evidence_bundle_retention_custody_audit.trust_banner if latest_evidence_bundle_retention_custody_audit else None,
        latest_evidence_bundle_retention_custody_audit_sha256=latest_evidence_bundle_retention_custody_audit.artifact_sha256 if latest_evidence_bundle_retention_custody_audit else None,
        evidence_bundle_retention_custody_audit_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_audits),
        evidence_bundle_retention_custody_audit_verification_count=len(evidence_bundle_retention_custody_audit_verifications),
        latest_evidence_bundle_retention_custody_audit_verification_at_utc=latest_evidence_bundle_retention_custody_audit_verification.generated_at_utc if latest_evidence_bundle_retention_custody_audit_verification else None,
        latest_evidence_bundle_retention_custody_audit_verification_status=latest_evidence_bundle_retention_custody_audit_verification.verification_status if latest_evidence_bundle_retention_custody_audit_verification else None,
        latest_evidence_bundle_retention_custody_audit_verification_trust_banner=latest_evidence_bundle_retention_custody_audit_verification.trust_banner if latest_evidence_bundle_retention_custody_audit_verification else None,
        latest_evidence_bundle_retention_custody_audit_verification_sha256=latest_evidence_bundle_retention_custody_audit_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_audit_verification else None,
        evidence_bundle_retention_custody_audit_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_audit_verifications),
        evidence_bundle_retention_custody_continuity_count=len(evidence_bundle_retention_custody_continuities),
        latest_evidence_bundle_retention_custody_continuity_at_utc=latest_evidence_bundle_retention_custody_continuity.generated_at_utc if latest_evidence_bundle_retention_custody_continuity else None,
        latest_evidence_bundle_retention_custody_continuity_status=latest_evidence_bundle_retention_custody_continuity.continuity_status if latest_evidence_bundle_retention_custody_continuity else None,
        latest_evidence_bundle_retention_custody_continuity_trust_banner=latest_evidence_bundle_retention_custody_continuity.trust_banner if latest_evidence_bundle_retention_custody_continuity else None,
        latest_evidence_bundle_retention_custody_continuity_sha256=latest_evidence_bundle_retention_custody_continuity.artifact_sha256 if latest_evidence_bundle_retention_custody_continuity else None,
        evidence_bundle_retention_custody_continuity_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_continuities),
        evidence_bundle_retention_custody_continuity_verification_count=len(evidence_bundle_retention_custody_continuity_verifications),
        latest_evidence_bundle_retention_custody_continuity_verification_at_utc=latest_evidence_bundle_retention_custody_continuity_verification.generated_at_utc if latest_evidence_bundle_retention_custody_continuity_verification else None,
        latest_evidence_bundle_retention_custody_continuity_verification_status=latest_evidence_bundle_retention_custody_continuity_verification.verification_status if latest_evidence_bundle_retention_custody_continuity_verification else None,
        latest_evidence_bundle_retention_custody_continuity_verification_trust_banner=latest_evidence_bundle_retention_custody_continuity_verification.trust_banner if latest_evidence_bundle_retention_custody_continuity_verification else None,
        latest_evidence_bundle_retention_custody_continuity_verification_sha256=latest_evidence_bundle_retention_custody_continuity_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_continuity_verification else None,
        evidence_bundle_retention_custody_continuity_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_continuity_verifications),
        evidence_bundle_retention_custody_review_count=len(evidence_bundle_retention_custody_reviews),
        latest_evidence_bundle_retention_custody_review_at_utc=latest_evidence_bundle_retention_custody_review.generated_at_utc if latest_evidence_bundle_retention_custody_review else None,
        latest_evidence_bundle_retention_custody_review_status=latest_evidence_bundle_retention_custody_review.review_status if latest_evidence_bundle_retention_custody_review else None,
        latest_evidence_bundle_retention_custody_review_trust_banner=latest_evidence_bundle_retention_custody_review.trust_banner if latest_evidence_bundle_retention_custody_review else None,
        latest_evidence_bundle_retention_custody_review_sha256=latest_evidence_bundle_retention_custody_review.artifact_sha256 if latest_evidence_bundle_retention_custody_review else None,
        evidence_bundle_retention_custody_review_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_reviews),
        evidence_bundle_retention_custody_review_verification_count=len(evidence_bundle_retention_custody_review_verifications),
        latest_evidence_bundle_retention_custody_review_verification_at_utc=latest_evidence_bundle_retention_custody_review_verification.generated_at_utc if latest_evidence_bundle_retention_custody_review_verification else None,
        latest_evidence_bundle_retention_custody_review_verification_status=latest_evidence_bundle_retention_custody_review_verification.verification_status if latest_evidence_bundle_retention_custody_review_verification else None,
        latest_evidence_bundle_retention_custody_review_verification_trust_banner=latest_evidence_bundle_retention_custody_review_verification.trust_banner if latest_evidence_bundle_retention_custody_review_verification else None,
        latest_evidence_bundle_retention_custody_review_verification_sha256=latest_evidence_bundle_retention_custody_review_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_review_verification else None,
        evidence_bundle_retention_custody_review_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_review_verifications),
        evidence_bundle_retention_custody_renewal_count=len(evidence_bundle_retention_custody_renewals),
        latest_evidence_bundle_retention_custody_renewal_at_utc=latest_evidence_bundle_retention_custody_renewal.generated_at_utc if latest_evidence_bundle_retention_custody_renewal else None,
        latest_evidence_bundle_retention_custody_renewal_status=latest_evidence_bundle_retention_custody_renewal.renewal_status if latest_evidence_bundle_retention_custody_renewal else None,
        latest_evidence_bundle_retention_custody_renewal_trust_banner=latest_evidence_bundle_retention_custody_renewal.trust_banner if latest_evidence_bundle_retention_custody_renewal else None,
        latest_evidence_bundle_retention_custody_renewal_sha256=latest_evidence_bundle_retention_custody_renewal.artifact_sha256 if latest_evidence_bundle_retention_custody_renewal else None,
        evidence_bundle_retention_custody_renewal_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_renewals),
        evidence_bundle_retention_custody_renewal_verification_count=len(evidence_bundle_retention_custody_renewal_verifications),
        latest_evidence_bundle_retention_custody_renewal_verification_at_utc=latest_evidence_bundle_retention_custody_renewal_verification.generated_at_utc if latest_evidence_bundle_retention_custody_renewal_verification else None,
        latest_evidence_bundle_retention_custody_renewal_verification_status=latest_evidence_bundle_retention_custody_renewal_verification.verification_status if latest_evidence_bundle_retention_custody_renewal_verification else None,
        latest_evidence_bundle_retention_custody_renewal_verification_trust_banner=latest_evidence_bundle_retention_custody_renewal_verification.trust_banner if latest_evidence_bundle_retention_custody_renewal_verification else None,
        latest_evidence_bundle_retention_custody_renewal_verification_sha256=latest_evidence_bundle_retention_custody_renewal_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_renewal_verification else None,
        evidence_bundle_retention_custody_renewal_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_renewal_verifications),
        evidence_bundle_retention_custody_schedule_count=len(evidence_bundle_retention_custody_schedules),
        latest_evidence_bundle_retention_custody_schedule_at_utc=latest_evidence_bundle_retention_custody_schedule.generated_at_utc if latest_evidence_bundle_retention_custody_schedule else None,
        latest_evidence_bundle_retention_custody_schedule_status=latest_evidence_bundle_retention_custody_schedule.schedule_status if latest_evidence_bundle_retention_custody_schedule else None,
        latest_evidence_bundle_retention_custody_schedule_trust_banner=latest_evidence_bundle_retention_custody_schedule.trust_banner if latest_evidence_bundle_retention_custody_schedule else None,
        latest_evidence_bundle_retention_custody_schedule_sha256=latest_evidence_bundle_retention_custody_schedule.artifact_sha256 if latest_evidence_bundle_retention_custody_schedule else None,
        latest_evidence_bundle_retention_custody_schedule_due_at_utc=latest_evidence_bundle_retention_custody_schedule.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_schedule else None,
        evidence_bundle_retention_custody_schedule_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_schedules),
        evidence_bundle_retention_custody_schedule_verification_count=len(evidence_bundle_retention_custody_schedule_verifications),
        latest_evidence_bundle_retention_custody_schedule_verification_at_utc=latest_evidence_bundle_retention_custody_schedule_verification.generated_at_utc if latest_evidence_bundle_retention_custody_schedule_verification else None,
        latest_evidence_bundle_retention_custody_schedule_verification_status=latest_evidence_bundle_retention_custody_schedule_verification.verification_status if latest_evidence_bundle_retention_custody_schedule_verification else None,
        latest_evidence_bundle_retention_custody_schedule_verification_trust_banner=latest_evidence_bundle_retention_custody_schedule_verification.trust_banner if latest_evidence_bundle_retention_custody_schedule_verification else None,
        latest_evidence_bundle_retention_custody_schedule_verification_sha256=latest_evidence_bundle_retention_custody_schedule_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_schedule_verification else None,
        latest_evidence_bundle_retention_custody_schedule_verification_due_at_utc=latest_evidence_bundle_retention_custody_schedule_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_schedule_verification else None,
        evidence_bundle_retention_custody_schedule_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_schedule_verifications),
        evidence_bundle_retention_custody_notice_count=len(evidence_bundle_retention_custody_notices),
        latest_evidence_bundle_retention_custody_notice_at_utc=latest_evidence_bundle_retention_custody_notice.generated_at_utc if latest_evidence_bundle_retention_custody_notice else None,
        latest_evidence_bundle_retention_custody_notice_status=latest_evidence_bundle_retention_custody_notice.notice_status if latest_evidence_bundle_retention_custody_notice else None,
        latest_evidence_bundle_retention_custody_notice_trust_banner=latest_evidence_bundle_retention_custody_notice.trust_banner if latest_evidence_bundle_retention_custody_notice else None,
        latest_evidence_bundle_retention_custody_notice_sha256=latest_evidence_bundle_retention_custody_notice.artifact_sha256 if latest_evidence_bundle_retention_custody_notice else None,
        latest_evidence_bundle_retention_custody_notice_due_at_utc=latest_evidence_bundle_retention_custody_notice.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_notice else None,
        evidence_bundle_retention_custody_notice_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_notices),
        evidence_bundle_retention_custody_notice_verification_count=len(evidence_bundle_retention_custody_notice_verifications),
        latest_evidence_bundle_retention_custody_notice_verification_at_utc=latest_evidence_bundle_retention_custody_notice_verification.generated_at_utc if latest_evidence_bundle_retention_custody_notice_verification else None,
        latest_evidence_bundle_retention_custody_notice_verification_status=latest_evidence_bundle_retention_custody_notice_verification.verification_status if latest_evidence_bundle_retention_custody_notice_verification else None,
        latest_evidence_bundle_retention_custody_notice_verification_trust_banner=latest_evidence_bundle_retention_custody_notice_verification.trust_banner if latest_evidence_bundle_retention_custody_notice_verification else None,
        latest_evidence_bundle_retention_custody_notice_verification_sha256=latest_evidence_bundle_retention_custody_notice_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_notice_verification else None,
        latest_evidence_bundle_retention_custody_notice_verification_due_at_utc=latest_evidence_bundle_retention_custody_notice_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_notice_verification else None,
        evidence_bundle_retention_custody_notice_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_notice_verifications),
        evidence_bundle_retention_custody_acknowledgment_count=len(evidence_bundle_retention_custody_acknowledgments),
        latest_evidence_bundle_retention_custody_acknowledgment_at_utc=latest_evidence_bundle_retention_custody_acknowledgment.generated_at_utc if latest_evidence_bundle_retention_custody_acknowledgment else None,
        latest_evidence_bundle_retention_custody_acknowledgment_status=latest_evidence_bundle_retention_custody_acknowledgment.acknowledgment_status if latest_evidence_bundle_retention_custody_acknowledgment else None,
        latest_evidence_bundle_retention_custody_acknowledgment_trust_banner=latest_evidence_bundle_retention_custody_acknowledgment.trust_banner if latest_evidence_bundle_retention_custody_acknowledgment else None,
        latest_evidence_bundle_retention_custody_acknowledgment_sha256=latest_evidence_bundle_retention_custody_acknowledgment.artifact_sha256 if latest_evidence_bundle_retention_custody_acknowledgment else None,
        latest_evidence_bundle_retention_custody_acknowledgment_due_at_utc=latest_evidence_bundle_retention_custody_acknowledgment.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_acknowledgment else None,
        evidence_bundle_retention_custody_acknowledgment_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_acknowledgments),
        evidence_bundle_retention_custody_acknowledgment_verification_count=len(evidence_bundle_retention_custody_acknowledgment_verifications),
        latest_evidence_bundle_retention_custody_acknowledgment_verification_at_utc=latest_evidence_bundle_retention_custody_acknowledgment_verification.generated_at_utc if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
        latest_evidence_bundle_retention_custody_acknowledgment_verification_status=latest_evidence_bundle_retention_custody_acknowledgment_verification.verification_status if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
        latest_evidence_bundle_retention_custody_acknowledgment_verification_trust_banner=latest_evidence_bundle_retention_custody_acknowledgment_verification.trust_banner if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
        latest_evidence_bundle_retention_custody_acknowledgment_verification_sha256=latest_evidence_bundle_retention_custody_acknowledgment_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
        latest_evidence_bundle_retention_custody_acknowledgment_verification_due_at_utc=latest_evidence_bundle_retention_custody_acknowledgment_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_acknowledgment_verification else None,
        evidence_bundle_retention_custody_acknowledgment_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_acknowledgment_verifications),
        evidence_bundle_retention_custody_completion_count=len(evidence_bundle_retention_custody_completions),
        latest_evidence_bundle_retention_custody_completion_at_utc=latest_evidence_bundle_retention_custody_completion.generated_at_utc if latest_evidence_bundle_retention_custody_completion else None,
        latest_evidence_bundle_retention_custody_completion_status=latest_evidence_bundle_retention_custody_completion.completion_status if latest_evidence_bundle_retention_custody_completion else None,
        latest_evidence_bundle_retention_custody_completion_trust_banner=latest_evidence_bundle_retention_custody_completion.trust_banner if latest_evidence_bundle_retention_custody_completion else None,
        latest_evidence_bundle_retention_custody_completion_sha256=latest_evidence_bundle_retention_custody_completion.artifact_sha256 if latest_evidence_bundle_retention_custody_completion else None,
        latest_evidence_bundle_retention_custody_completion_due_at_utc=latest_evidence_bundle_retention_custody_completion.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_completion else None,
        evidence_bundle_retention_custody_completion_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_completions),
        evidence_bundle_retention_custody_completion_verification_count=len(evidence_bundle_retention_custody_completion_verifications),
        latest_evidence_bundle_retention_custody_completion_verification_at_utc=latest_evidence_bundle_retention_custody_completion_verification.generated_at_utc if latest_evidence_bundle_retention_custody_completion_verification else None,
        latest_evidence_bundle_retention_custody_completion_verification_status=latest_evidence_bundle_retention_custody_completion_verification.verification_status if latest_evidence_bundle_retention_custody_completion_verification else None,
        latest_evidence_bundle_retention_custody_completion_verification_trust_banner=latest_evidence_bundle_retention_custody_completion_verification.trust_banner if latest_evidence_bundle_retention_custody_completion_verification else None,
        latest_evidence_bundle_retention_custody_completion_verification_sha256=latest_evidence_bundle_retention_custody_completion_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_completion_verification else None,
        latest_evidence_bundle_retention_custody_completion_verification_due_at_utc=latest_evidence_bundle_retention_custody_completion_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_completion_verification else None,
        evidence_bundle_retention_custody_completion_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_completion_verifications),
        evidence_bundle_retention_custody_closeout_count=len(evidence_bundle_retention_custody_closeouts),
        latest_evidence_bundle_retention_custody_closeout_at_utc=latest_evidence_bundle_retention_custody_closeout.generated_at_utc if latest_evidence_bundle_retention_custody_closeout else None,
        latest_evidence_bundle_retention_custody_closeout_status=latest_evidence_bundle_retention_custody_closeout.closeout_status if latest_evidence_bundle_retention_custody_closeout else None,
        latest_evidence_bundle_retention_custody_closeout_trust_banner=latest_evidence_bundle_retention_custody_closeout.trust_banner if latest_evidence_bundle_retention_custody_closeout else None,
        latest_evidence_bundle_retention_custody_closeout_sha256=latest_evidence_bundle_retention_custody_closeout.artifact_sha256 if latest_evidence_bundle_retention_custody_closeout else None,
        latest_evidence_bundle_retention_custody_closeout_due_at_utc=latest_evidence_bundle_retention_custody_closeout.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_closeout else None,
        evidence_bundle_retention_custody_closeout_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_closeouts),
        evidence_bundle_retention_custody_closeout_verification_count=len(evidence_bundle_retention_custody_closeout_verifications),
        latest_evidence_bundle_retention_custody_closeout_verification_at_utc=latest_evidence_bundle_retention_custody_closeout_verification.generated_at_utc if latest_evidence_bundle_retention_custody_closeout_verification else None,
        latest_evidence_bundle_retention_custody_closeout_verification_status=latest_evidence_bundle_retention_custody_closeout_verification.verification_status if latest_evidence_bundle_retention_custody_closeout_verification else None,
        latest_evidence_bundle_retention_custody_closeout_verification_trust_banner=latest_evidence_bundle_retention_custody_closeout_verification.trust_banner if latest_evidence_bundle_retention_custody_closeout_verification else None,
        latest_evidence_bundle_retention_custody_closeout_verification_sha256=latest_evidence_bundle_retention_custody_closeout_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_closeout_verification else None,
        latest_evidence_bundle_retention_custody_closeout_verification_due_at_utc=latest_evidence_bundle_retention_custody_closeout_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_closeout_verification else None,
        evidence_bundle_retention_custody_closeout_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_closeout_verifications),
        evidence_bundle_retention_custody_archive_count=len(evidence_bundle_retention_custody_archives),
        latest_evidence_bundle_retention_custody_archive_at_utc=latest_evidence_bundle_retention_custody_archive.generated_at_utc if latest_evidence_bundle_retention_custody_archive else None,
        latest_evidence_bundle_retention_custody_archive_status=latest_evidence_bundle_retention_custody_archive.archive_status if latest_evidence_bundle_retention_custody_archive else None,
        latest_evidence_bundle_retention_custody_archive_trust_banner=latest_evidence_bundle_retention_custody_archive.trust_banner if latest_evidence_bundle_retention_custody_archive else None,
        latest_evidence_bundle_retention_custody_archive_sha256=latest_evidence_bundle_retention_custody_archive.artifact_sha256 if latest_evidence_bundle_retention_custody_archive else None,
        latest_evidence_bundle_retention_custody_archive_due_at_utc=latest_evidence_bundle_retention_custody_archive.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_archive else None,
        evidence_bundle_retention_custody_archive_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_archives),
        evidence_bundle_retention_custody_archive_verification_count=len(evidence_bundle_retention_custody_archive_verifications),
        latest_evidence_bundle_retention_custody_archive_verification_at_utc=latest_evidence_bundle_retention_custody_archive_verification.generated_at_utc if latest_evidence_bundle_retention_custody_archive_verification else None,
        latest_evidence_bundle_retention_custody_archive_verification_status=latest_evidence_bundle_retention_custody_archive_verification.verification_status if latest_evidence_bundle_retention_custody_archive_verification else None,
        latest_evidence_bundle_retention_custody_archive_verification_trust_banner=latest_evidence_bundle_retention_custody_archive_verification.trust_banner if latest_evidence_bundle_retention_custody_archive_verification else None,
        latest_evidence_bundle_retention_custody_archive_verification_sha256=latest_evidence_bundle_retention_custody_archive_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_archive_verification else None,
        latest_evidence_bundle_retention_custody_archive_verification_due_at_utc=latest_evidence_bundle_retention_custody_archive_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_archive_verification else None,
        evidence_bundle_retention_custody_archive_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_archive_verifications),
        evidence_bundle_retention_custody_retrieval_count=len(evidence_bundle_retention_custody_retrievals),
        latest_evidence_bundle_retention_custody_retrieval_at_utc=latest_evidence_bundle_retention_custody_retrieval.generated_at_utc if latest_evidence_bundle_retention_custody_retrieval else None,
        latest_evidence_bundle_retention_custody_retrieval_status=latest_evidence_bundle_retention_custody_retrieval.retrieval_status if latest_evidence_bundle_retention_custody_retrieval else None,
        latest_evidence_bundle_retention_custody_retrieval_trust_banner=latest_evidence_bundle_retention_custody_retrieval.trust_banner if latest_evidence_bundle_retention_custody_retrieval else None,
        latest_evidence_bundle_retention_custody_retrieval_sha256=latest_evidence_bundle_retention_custody_retrieval.artifact_sha256 if latest_evidence_bundle_retention_custody_retrieval else None,
        latest_evidence_bundle_retention_custody_retrieval_due_at_utc=latest_evidence_bundle_retention_custody_retrieval.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_retrieval else None,
        evidence_bundle_retention_custody_retrieval_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_retrievals),
        evidence_bundle_retention_custody_retrieval_verification_count=len(evidence_bundle_retention_custody_retrieval_verifications),
        latest_evidence_bundle_retention_custody_retrieval_verification_at_utc=latest_evidence_bundle_retention_custody_retrieval_verification.generated_at_utc if latest_evidence_bundle_retention_custody_retrieval_verification else None,
        latest_evidence_bundle_retention_custody_retrieval_verification_status=latest_evidence_bundle_retention_custody_retrieval_verification.verification_status if latest_evidence_bundle_retention_custody_retrieval_verification else None,
        latest_evidence_bundle_retention_custody_retrieval_verification_trust_banner=latest_evidence_bundle_retention_custody_retrieval_verification.trust_banner if latest_evidence_bundle_retention_custody_retrieval_verification else None,
        latest_evidence_bundle_retention_custody_retrieval_verification_sha256=latest_evidence_bundle_retention_custody_retrieval_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_retrieval_verification else None,
        latest_evidence_bundle_retention_custody_retrieval_verification_due_at_utc=latest_evidence_bundle_retention_custody_retrieval_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_retrieval_verification else None,
        evidence_bundle_retention_custody_retrieval_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_retrieval_verifications),
        evidence_bundle_retention_custody_return_count=len(evidence_bundle_retention_custody_returns),
        latest_evidence_bundle_retention_custody_return_at_utc=latest_evidence_bundle_retention_custody_return.generated_at_utc if latest_evidence_bundle_retention_custody_return else None,
        latest_evidence_bundle_retention_custody_return_status=latest_evidence_bundle_retention_custody_return.return_status if latest_evidence_bundle_retention_custody_return else None,
        latest_evidence_bundle_retention_custody_return_trust_banner=latest_evidence_bundle_retention_custody_return.trust_banner if latest_evidence_bundle_retention_custody_return else None,
        latest_evidence_bundle_retention_custody_return_sha256=latest_evidence_bundle_retention_custody_return.artifact_sha256 if latest_evidence_bundle_retention_custody_return else None,
        latest_evidence_bundle_retention_custody_return_due_at_utc=latest_evidence_bundle_retention_custody_return.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_return else None,
        evidence_bundle_retention_custody_return_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_returns),
        evidence_bundle_retention_custody_return_verification_count=len(evidence_bundle_retention_custody_return_verifications),
        latest_evidence_bundle_retention_custody_return_verification_at_utc=latest_evidence_bundle_retention_custody_return_verification.generated_at_utc if latest_evidence_bundle_retention_custody_return_verification else None,
        latest_evidence_bundle_retention_custody_return_verification_status=latest_evidence_bundle_retention_custody_return_verification.verification_status if latest_evidence_bundle_retention_custody_return_verification else None,
        latest_evidence_bundle_retention_custody_return_verification_trust_banner=latest_evidence_bundle_retention_custody_return_verification.trust_banner if latest_evidence_bundle_retention_custody_return_verification else None,
        latest_evidence_bundle_retention_custody_return_verification_sha256=latest_evidence_bundle_retention_custody_return_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_return_verification else None,
        latest_evidence_bundle_retention_custody_return_verification_due_at_utc=latest_evidence_bundle_retention_custody_return_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_return_verification else None,
        evidence_bundle_retention_custody_return_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_return_verifications),
        evidence_bundle_retention_custody_redeposit_count=len(evidence_bundle_retention_custody_redeposits),
        latest_evidence_bundle_retention_custody_redeposit_at_utc=latest_evidence_bundle_retention_custody_redeposit.generated_at_utc if latest_evidence_bundle_retention_custody_redeposit else None,
        latest_evidence_bundle_retention_custody_redeposit_status=latest_evidence_bundle_retention_custody_redeposit.redeposit_status if latest_evidence_bundle_retention_custody_redeposit else None,
        latest_evidence_bundle_retention_custody_redeposit_trust_banner=latest_evidence_bundle_retention_custody_redeposit.trust_banner if latest_evidence_bundle_retention_custody_redeposit else None,
        latest_evidence_bundle_retention_custody_redeposit_sha256=latest_evidence_bundle_retention_custody_redeposit.artifact_sha256 if latest_evidence_bundle_retention_custody_redeposit else None,
        latest_evidence_bundle_retention_custody_redeposit_due_at_utc=latest_evidence_bundle_retention_custody_redeposit.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_redeposit else None,
        evidence_bundle_retention_custody_redeposit_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_redeposits),
        evidence_bundle_retention_custody_redeposit_verification_count=len(evidence_bundle_retention_custody_redeposit_verifications),
        latest_evidence_bundle_retention_custody_redeposit_verification_at_utc=latest_evidence_bundle_retention_custody_redeposit_verification.generated_at_utc if latest_evidence_bundle_retention_custody_redeposit_verification else None,
        latest_evidence_bundle_retention_custody_redeposit_verification_status=latest_evidence_bundle_retention_custody_redeposit_verification.verification_status if latest_evidence_bundle_retention_custody_redeposit_verification else None,
        latest_evidence_bundle_retention_custody_redeposit_verification_trust_banner=latest_evidence_bundle_retention_custody_redeposit_verification.trust_banner if latest_evidence_bundle_retention_custody_redeposit_verification else None,
        latest_evidence_bundle_retention_custody_redeposit_verification_sha256=latest_evidence_bundle_retention_custody_redeposit_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_redeposit_verification else None,
        latest_evidence_bundle_retention_custody_redeposit_verification_due_at_utc=latest_evidence_bundle_retention_custody_redeposit_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_redeposit_verification else None,
        evidence_bundle_retention_custody_redeposit_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_redeposit_verifications),
        evidence_bundle_retention_custody_inventory_count=len(evidence_bundle_retention_custody_inventories),
        latest_evidence_bundle_retention_custody_inventory_at_utc=latest_evidence_bundle_retention_custody_inventory.generated_at_utc if latest_evidence_bundle_retention_custody_inventory else None,
        latest_evidence_bundle_retention_custody_inventory_status=latest_evidence_bundle_retention_custody_inventory.inventory_status if latest_evidence_bundle_retention_custody_inventory else None,
        latest_evidence_bundle_retention_custody_inventory_trust_banner=latest_evidence_bundle_retention_custody_inventory.trust_banner if latest_evidence_bundle_retention_custody_inventory else None,
        latest_evidence_bundle_retention_custody_inventory_sha256=latest_evidence_bundle_retention_custody_inventory.artifact_sha256 if latest_evidence_bundle_retention_custody_inventory else None,
        latest_evidence_bundle_retention_custody_inventory_due_at_utc=latest_evidence_bundle_retention_custody_inventory.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_inventory else None,
        evidence_bundle_retention_custody_inventory_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_inventories),
        evidence_bundle_retention_custody_inventory_verification_count=len(evidence_bundle_retention_custody_inventory_verifications),
        latest_evidence_bundle_retention_custody_inventory_verification_at_utc=latest_evidence_bundle_retention_custody_inventory_verification.generated_at_utc if latest_evidence_bundle_retention_custody_inventory_verification else None,
        latest_evidence_bundle_retention_custody_inventory_verification_status=latest_evidence_bundle_retention_custody_inventory_verification.verification_status if latest_evidence_bundle_retention_custody_inventory_verification else None,
        latest_evidence_bundle_retention_custody_inventory_verification_trust_banner=latest_evidence_bundle_retention_custody_inventory_verification.trust_banner if latest_evidence_bundle_retention_custody_inventory_verification else None,
        latest_evidence_bundle_retention_custody_inventory_verification_sha256=latest_evidence_bundle_retention_custody_inventory_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_inventory_verification else None,
        latest_evidence_bundle_retention_custody_inventory_verification_due_at_utc=latest_evidence_bundle_retention_custody_inventory_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_inventory_verification else None,
        evidence_bundle_retention_custody_inventory_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_inventory_verifications),
        evidence_bundle_retention_custody_reconciliation_count=len(evidence_bundle_retention_custody_reconciliations),
        latest_evidence_bundle_retention_custody_reconciliation_at_utc=latest_evidence_bundle_retention_custody_reconciliation.generated_at_utc if latest_evidence_bundle_retention_custody_reconciliation else None,
        latest_evidence_bundle_retention_custody_reconciliation_status=latest_evidence_bundle_retention_custody_reconciliation.reconciliation_status if latest_evidence_bundle_retention_custody_reconciliation else None,
        latest_evidence_bundle_retention_custody_reconciliation_trust_banner=latest_evidence_bundle_retention_custody_reconciliation.trust_banner if latest_evidence_bundle_retention_custody_reconciliation else None,
        latest_evidence_bundle_retention_custody_reconciliation_sha256=latest_evidence_bundle_retention_custody_reconciliation.artifact_sha256 if latest_evidence_bundle_retention_custody_reconciliation else None,
        latest_evidence_bundle_retention_custody_reconciliation_due_at_utc=latest_evidence_bundle_retention_custody_reconciliation.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_reconciliation else None,
        evidence_bundle_retention_custody_reconciliation_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_reconciliations),
        evidence_bundle_retention_custody_reconciliation_verification_count=len(evidence_bundle_retention_custody_reconciliation_verifications),
        latest_evidence_bundle_retention_custody_reconciliation_verification_at_utc=latest_evidence_bundle_retention_custody_reconciliation_verification.generated_at_utc if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
        latest_evidence_bundle_retention_custody_reconciliation_verification_status=latest_evidence_bundle_retention_custody_reconciliation_verification.verification_status if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
        latest_evidence_bundle_retention_custody_reconciliation_verification_trust_banner=latest_evidence_bundle_retention_custody_reconciliation_verification.trust_banner if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
        latest_evidence_bundle_retention_custody_reconciliation_verification_sha256=latest_evidence_bundle_retention_custody_reconciliation_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
        latest_evidence_bundle_retention_custody_reconciliation_verification_due_at_utc=latest_evidence_bundle_retention_custody_reconciliation_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_reconciliation_verification else None,
        evidence_bundle_retention_custody_reconciliation_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_reconciliation_verifications),
        evidence_bundle_retention_custody_certification_count=len(evidence_bundle_retention_custody_certifications),
        latest_evidence_bundle_retention_custody_certification_at_utc=latest_evidence_bundle_retention_custody_certification.generated_at_utc if latest_evidence_bundle_retention_custody_certification else None,
        latest_evidence_bundle_retention_custody_certification_status=latest_evidence_bundle_retention_custody_certification.certification_status if latest_evidence_bundle_retention_custody_certification else None,
        latest_evidence_bundle_retention_custody_certification_trust_banner=latest_evidence_bundle_retention_custody_certification.trust_banner if latest_evidence_bundle_retention_custody_certification else None,
        latest_evidence_bundle_retention_custody_certification_sha256=latest_evidence_bundle_retention_custody_certification.artifact_sha256 if latest_evidence_bundle_retention_custody_certification else None,
        latest_evidence_bundle_retention_custody_certification_due_at_utc=latest_evidence_bundle_retention_custody_certification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_certification else None,
        evidence_bundle_retention_custody_certification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_certifications),
        evidence_bundle_retention_custody_certification_verification_count=len(evidence_bundle_retention_custody_certification_verifications),
        latest_evidence_bundle_retention_custody_certification_verification_at_utc=latest_evidence_bundle_retention_custody_certification_verification.generated_at_utc if latest_evidence_bundle_retention_custody_certification_verification else None,
        latest_evidence_bundle_retention_custody_certification_verification_status=latest_evidence_bundle_retention_custody_certification_verification.verification_status if latest_evidence_bundle_retention_custody_certification_verification else None,
        latest_evidence_bundle_retention_custody_certification_verification_trust_banner=latest_evidence_bundle_retention_custody_certification_verification.trust_banner if latest_evidence_bundle_retention_custody_certification_verification else None,
        latest_evidence_bundle_retention_custody_certification_verification_sha256=latest_evidence_bundle_retention_custody_certification_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_certification_verification else None,
        latest_evidence_bundle_retention_custody_certification_verification_due_at_utc=latest_evidence_bundle_retention_custody_certification_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_certification_verification else None,
        evidence_bundle_retention_custody_certification_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_certification_verifications),
        evidence_bundle_retention_custody_attestation_count=len(evidence_bundle_retention_custody_attestations),
        latest_evidence_bundle_retention_custody_attestation_at_utc=latest_evidence_bundle_retention_custody_attestation.generated_at_utc if latest_evidence_bundle_retention_custody_attestation else None,
        latest_evidence_bundle_retention_custody_attestation_status=latest_evidence_bundle_retention_custody_attestation.attestation_status if latest_evidence_bundle_retention_custody_attestation else None,
        latest_evidence_bundle_retention_custody_attestation_trust_banner=latest_evidence_bundle_retention_custody_attestation.trust_banner if latest_evidence_bundle_retention_custody_attestation else None,
        latest_evidence_bundle_retention_custody_attestation_sha256=latest_evidence_bundle_retention_custody_attestation.artifact_sha256 if latest_evidence_bundle_retention_custody_attestation else None,
        latest_evidence_bundle_retention_custody_attestation_due_at_utc=latest_evidence_bundle_retention_custody_attestation.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_attestation else None,
        evidence_bundle_retention_custody_attestation_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_attestations),
        evidence_bundle_retention_custody_attestation_verification_count=len(evidence_bundle_retention_custody_attestation_verifications),
        latest_evidence_bundle_retention_custody_attestation_verification_at_utc=latest_evidence_bundle_retention_custody_attestation_verification.generated_at_utc if latest_evidence_bundle_retention_custody_attestation_verification else None,
        latest_evidence_bundle_retention_custody_attestation_verification_status=latest_evidence_bundle_retention_custody_attestation_verification.verification_status if latest_evidence_bundle_retention_custody_attestation_verification else None,
        latest_evidence_bundle_retention_custody_attestation_verification_trust_banner=latest_evidence_bundle_retention_custody_attestation_verification.trust_banner if latest_evidence_bundle_retention_custody_attestation_verification else None,
        latest_evidence_bundle_retention_custody_attestation_verification_sha256=latest_evidence_bundle_retention_custody_attestation_verification.artifact_sha256 if latest_evidence_bundle_retention_custody_attestation_verification else None,
        latest_evidence_bundle_retention_custody_attestation_verification_due_at_utc=latest_evidence_bundle_retention_custody_attestation_verification.next_renewal_due_at_utc if latest_evidence_bundle_retention_custody_attestation_verification else None,
        evidence_bundle_retention_custody_attestation_verification_blocker_count=sum(row.blocker_count for row in evidence_bundle_retention_custody_attestation_verifications),
        latest_dry_run_artifact_at_utc=next((row.retrieved_at_utc for row in dry_run_artifacts if row.retrieved_at_utc), None),
        latest_dry_run_source_selection_sha256=replay_source_sha,
        selected_intent_dry_run_match=replay_match,
        selected_intent_dry_run_status=replay_status,
        selected_intent_count=selected_count,
        latest_selected_tracking_id=str((selected_raw or {}).get("tracking_id") or "") or None,
        latest_selected_intent_at_utc=str((selected_raw or {}).get("generated_at_utc") or "") or None,
        selected_intent_artifact_path=str((selected_raw or {}).get("artifact_path") or "") or None,
        broker_ready=broker_policy == "PAPER_READY",
        tracking_present=tracking_present,
        paper_submission_capability="CLI_ONLY",
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
        latest_evidence_bundle=latest_evidence_bundle,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        latest_evidence_bundle_rotation=latest_evidence_bundle_rotation,
        latest_evidence_bundle_rotation_execution=latest_evidence_bundle_rotation_execution,
        latest_evidence_bundle_attestation=latest_evidence_bundle_attestation,
        latest_evidence_bundle_attestation_verification=latest_evidence_bundle_attestation_verification,
        latest_evidence_bundle_closure=latest_evidence_bundle_closure,
        latest_evidence_bundle_closure_verification=latest_evidence_bundle_closure_verification,
        latest_evidence_bundle_export_manifest=latest_evidence_bundle_export_manifest,
        latest_evidence_bundle_export_verification=latest_evidence_bundle_export_verification,
        latest_evidence_bundle_retention_receipt=latest_evidence_bundle_retention_receipt,
        latest_evidence_bundle_retention_verification=latest_evidence_bundle_retention_verification,
        latest_evidence_bundle_retention_signoff=latest_evidence_bundle_retention_signoff,
        latest_evidence_bundle_retention_signoff_verification=latest_evidence_bundle_retention_signoff_verification,
        latest_evidence_bundle_retention_handoff=latest_evidence_bundle_retention_handoff,
        latest_evidence_bundle_retention_handoff_verification=latest_evidence_bundle_retention_handoff_verification,
        latest_evidence_bundle_retention_handoff_acceptance=latest_evidence_bundle_retention_handoff_acceptance,
        latest_evidence_bundle_retention_handoff_acceptance_verification=latest_evidence_bundle_retention_handoff_acceptance_verification,
        latest_evidence_bundle_retention_custody_register=latest_evidence_bundle_retention_custody_register,
        latest_evidence_bundle_retention_custody_register_verification=latest_evidence_bundle_retention_custody_register_verification,
        latest_evidence_bundle_retention_custody_seal=latest_evidence_bundle_retention_custody_seal,
        latest_evidence_bundle_retention_custody_seal_verification=latest_evidence_bundle_retention_custody_seal_verification,
        latest_evidence_bundle_retention_custody_audit=latest_evidence_bundle_retention_custody_audit,
        latest_evidence_bundle_retention_custody_audit_verification=latest_evidence_bundle_retention_custody_audit_verification,
        latest_evidence_bundle_retention_custody_continuity=latest_evidence_bundle_retention_custody_continuity,
        latest_evidence_bundle_retention_custody_continuity_verification=latest_evidence_bundle_retention_custody_continuity_verification,
        latest_evidence_bundle_retention_custody_review=latest_evidence_bundle_retention_custody_review,
        latest_evidence_bundle_retention_custody_review_verification=latest_evidence_bundle_retention_custody_review_verification,
        latest_evidence_bundle_retention_custody_renewal=latest_evidence_bundle_retention_custody_renewal,
        latest_evidence_bundle_retention_custody_renewal_verification=latest_evidence_bundle_retention_custody_renewal_verification,
        latest_evidence_bundle_retention_custody_schedule=latest_evidence_bundle_retention_custody_schedule,
        latest_evidence_bundle_retention_custody_schedule_verification=latest_evidence_bundle_retention_custody_schedule_verification,
        latest_evidence_bundle_retention_custody_notice=latest_evidence_bundle_retention_custody_notice,
        latest_evidence_bundle_retention_custody_notice_verification=latest_evidence_bundle_retention_custody_notice_verification,
        latest_evidence_bundle_retention_custody_acknowledgment=latest_evidence_bundle_retention_custody_acknowledgment,
        latest_evidence_bundle_retention_custody_acknowledgment_verification=latest_evidence_bundle_retention_custody_acknowledgment_verification,
        latest_evidence_bundle_retention_custody_completion=latest_evidence_bundle_retention_custody_completion,
        latest_evidence_bundle_retention_custody_completion_verification=latest_evidence_bundle_retention_custody_completion_verification,
        latest_evidence_bundle_retention_custody_closeout=latest_evidence_bundle_retention_custody_closeout,
        latest_evidence_bundle_retention_custody_closeout_verification=latest_evidence_bundle_retention_custody_closeout_verification,
        latest_evidence_bundle_retention_custody_archive=latest_evidence_bundle_retention_custody_archive,
        latest_evidence_bundle_retention_custody_archive_verification=latest_evidence_bundle_retention_custody_archive_verification,
        latest_evidence_bundle_retention_custody_retrieval=latest_evidence_bundle_retention_custody_retrieval,
        latest_evidence_bundle_retention_custody_retrieval_verification=latest_evidence_bundle_retention_custody_retrieval_verification,
        latest_evidence_bundle_retention_custody_return=latest_evidence_bundle_retention_custody_return,
        latest_evidence_bundle_retention_custody_return_verification=latest_evidence_bundle_retention_custody_return_verification,
        latest_evidence_bundle_retention_custody_redeposit=latest_evidence_bundle_retention_custody_redeposit,
        latest_evidence_bundle_retention_custody_redeposit_verification=latest_evidence_bundle_retention_custody_redeposit_verification,
        latest_evidence_bundle_retention_custody_inventory=latest_evidence_bundle_retention_custody_inventory,
        latest_evidence_bundle_retention_custody_inventory_verification=latest_evidence_bundle_retention_custody_inventory_verification,
        latest_evidence_bundle_retention_custody_reconciliation=latest_evidence_bundle_retention_custody_reconciliation,
        latest_evidence_bundle_retention_custody_reconciliation_verification=latest_evidence_bundle_retention_custody_reconciliation_verification,
        latest_evidence_bundle_retention_custody_certification=latest_evidence_bundle_retention_custody_certification,
        latest_evidence_bundle_retention_custody_certification_verification=latest_evidence_bundle_retention_custody_certification_verification,
        latest_evidence_bundle_retention_custody_attestation=latest_evidence_bundle_retention_custody_attestation,
        latest_evidence_bundle_retention_custody_attestation_verification=latest_evidence_bundle_retention_custody_attestation_verification,
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
        dry_run_command_hint=str((selected_raw or {}).get("dry_run_command_hint") or "") or None,
        dry_run_results=dry_runs,
        freshness_gate=freshness_gate,
        journal_entries=journal,
        submission_receipts=submission_receipts,
        order_statuses=order_statuses,
        account_position_snapshot=position_snapshot,
        position_reconciliation=position_reconciliation,
        execution_timeline=execution_timeline,
        execution_timeline_summary=execution_timeline_summary,
        evidence_bundles=evidence_bundles,
        latest_evidence_bundle=latest_evidence_bundle,
        evidence_bundle_verifications=evidence_bundle_verifications,
        latest_evidence_bundle_verification=latest_evidence_bundle_verification,
        evidence_bundle_drifts=evidence_bundle_drifts,
        latest_evidence_bundle_drift=latest_evidence_bundle_drift,
        evidence_bundle_rotations=evidence_bundle_rotations,
        latest_evidence_bundle_rotation=latest_evidence_bundle_rotation,
        evidence_bundle_rotation_executions=evidence_bundle_rotation_executions,
        latest_evidence_bundle_rotation_execution=latest_evidence_bundle_rotation_execution,
        evidence_bundle_attestations=evidence_bundle_attestations,
        latest_evidence_bundle_attestation=latest_evidence_bundle_attestation,
        evidence_bundle_attestation_verifications=evidence_bundle_attestation_verifications,
        latest_evidence_bundle_attestation_verification=latest_evidence_bundle_attestation_verification,
        evidence_bundle_closures=evidence_bundle_closures,
        latest_evidence_bundle_closure=latest_evidence_bundle_closure,
        evidence_bundle_closure_verifications=evidence_bundle_closure_verifications,
        latest_evidence_bundle_closure_verification=latest_evidence_bundle_closure_verification,
        evidence_bundle_export_manifests=evidence_bundle_export_manifests,
        latest_evidence_bundle_export_manifest=latest_evidence_bundle_export_manifest,
        evidence_bundle_export_verifications=evidence_bundle_export_verifications,
        latest_evidence_bundle_export_verification=latest_evidence_bundle_export_verification,
        evidence_bundle_retention_receipts=evidence_bundle_retention_receipts,
        latest_evidence_bundle_retention_receipt=latest_evidence_bundle_retention_receipt,
        evidence_bundle_retention_verifications=evidence_bundle_retention_verifications,
        latest_evidence_bundle_retention_verification=latest_evidence_bundle_retention_verification,
        evidence_bundle_retention_signoffs=evidence_bundle_retention_signoffs,
        latest_evidence_bundle_retention_signoff=latest_evidence_bundle_retention_signoff,
        evidence_bundle_retention_signoff_verifications=evidence_bundle_retention_signoff_verifications,
        latest_evidence_bundle_retention_signoff_verification=latest_evidence_bundle_retention_signoff_verification,
        evidence_bundle_retention_handoffs=evidence_bundle_retention_handoffs,
        latest_evidence_bundle_retention_handoff=latest_evidence_bundle_retention_handoff,
        evidence_bundle_retention_handoff_verifications=evidence_bundle_retention_handoff_verifications,
        latest_evidence_bundle_retention_handoff_verification=latest_evidence_bundle_retention_handoff_verification,
        evidence_bundle_retention_handoff_acceptances=evidence_bundle_retention_handoff_acceptances,
        latest_evidence_bundle_retention_handoff_acceptance=latest_evidence_bundle_retention_handoff_acceptance,
        evidence_bundle_retention_handoff_acceptance_verifications=evidence_bundle_retention_handoff_acceptance_verifications,
        latest_evidence_bundle_retention_handoff_acceptance_verification=latest_evidence_bundle_retention_handoff_acceptance_verification,
        evidence_bundle_retention_custody_registers=evidence_bundle_retention_custody_registers,
        latest_evidence_bundle_retention_custody_register=latest_evidence_bundle_retention_custody_register,
        evidence_bundle_retention_custody_register_verifications=evidence_bundle_retention_custody_register_verifications,
        latest_evidence_bundle_retention_custody_register_verification=latest_evidence_bundle_retention_custody_register_verification,
        evidence_bundle_retention_custody_seals=evidence_bundle_retention_custody_seals,
        latest_evidence_bundle_retention_custody_seal=latest_evidence_bundle_retention_custody_seal,
        evidence_bundle_retention_custody_seal_verifications=evidence_bundle_retention_custody_seal_verifications,
        latest_evidence_bundle_retention_custody_seal_verification=latest_evidence_bundle_retention_custody_seal_verification,
        evidence_bundle_retention_custody_audits=evidence_bundle_retention_custody_audits,
        latest_evidence_bundle_retention_custody_audit=latest_evidence_bundle_retention_custody_audit,
        evidence_bundle_retention_custody_audit_verifications=evidence_bundle_retention_custody_audit_verifications,
        latest_evidence_bundle_retention_custody_audit_verification=latest_evidence_bundle_retention_custody_audit_verification,
        evidence_bundle_retention_custody_continuities=evidence_bundle_retention_custody_continuities,
        latest_evidence_bundle_retention_custody_continuity=latest_evidence_bundle_retention_custody_continuity,
        evidence_bundle_retention_custody_continuity_verifications=evidence_bundle_retention_custody_continuity_verifications,
        latest_evidence_bundle_retention_custody_continuity_verification=latest_evidence_bundle_retention_custody_continuity_verification,
        evidence_bundle_retention_custody_reviews=evidence_bundle_retention_custody_reviews,
        latest_evidence_bundle_retention_custody_review=latest_evidence_bundle_retention_custody_review,
        evidence_bundle_retention_custody_review_verifications=evidence_bundle_retention_custody_review_verifications,
        latest_evidence_bundle_retention_custody_review_verification=latest_evidence_bundle_retention_custody_review_verification,
        evidence_bundle_retention_custody_renewals=evidence_bundle_retention_custody_renewals,
        latest_evidence_bundle_retention_custody_renewal=latest_evidence_bundle_retention_custody_renewal,
        evidence_bundle_retention_custody_renewal_verifications=evidence_bundle_retention_custody_renewal_verifications,
        latest_evidence_bundle_retention_custody_renewal_verification=latest_evidence_bundle_retention_custody_renewal_verification,
        evidence_bundle_retention_custody_schedules=evidence_bundle_retention_custody_schedules,
        latest_evidence_bundle_retention_custody_schedule=latest_evidence_bundle_retention_custody_schedule,
        evidence_bundle_retention_custody_schedule_verifications=evidence_bundle_retention_custody_schedule_verifications,
        latest_evidence_bundle_retention_custody_schedule_verification=latest_evidence_bundle_retention_custody_schedule_verification,
        evidence_bundle_retention_custody_notices=evidence_bundle_retention_custody_notices,
        latest_evidence_bundle_retention_custody_notice=latest_evidence_bundle_retention_custody_notice,
        evidence_bundle_retention_custody_notice_verifications=evidence_bundle_retention_custody_notice_verifications,
        latest_evidence_bundle_retention_custody_notice_verification=latest_evidence_bundle_retention_custody_notice_verification,
        evidence_bundle_retention_custody_acknowledgments=evidence_bundle_retention_custody_acknowledgments,
        latest_evidence_bundle_retention_custody_acknowledgment=latest_evidence_bundle_retention_custody_acknowledgment,
        evidence_bundle_retention_custody_acknowledgment_verifications=evidence_bundle_retention_custody_acknowledgment_verifications,
        latest_evidence_bundle_retention_custody_acknowledgment_verification=latest_evidence_bundle_retention_custody_acknowledgment_verification,
        evidence_bundle_retention_custody_completions=evidence_bundle_retention_custody_completions,
        latest_evidence_bundle_retention_custody_completion=latest_evidence_bundle_retention_custody_completion,
        evidence_bundle_retention_custody_completion_verifications=evidence_bundle_retention_custody_completion_verifications,
        latest_evidence_bundle_retention_custody_completion_verification=latest_evidence_bundle_retention_custody_completion_verification,
        evidence_bundle_retention_custody_closeouts=evidence_bundle_retention_custody_closeouts,
        latest_evidence_bundle_retention_custody_closeout=latest_evidence_bundle_retention_custody_closeout,
        evidence_bundle_retention_custody_closeout_verifications=evidence_bundle_retention_custody_closeout_verifications,
        latest_evidence_bundle_retention_custody_closeout_verification=latest_evidence_bundle_retention_custody_closeout_verification,
        evidence_bundle_retention_custody_archives=evidence_bundle_retention_custody_archives,
        latest_evidence_bundle_retention_custody_archive=latest_evidence_bundle_retention_custody_archive,
        evidence_bundle_retention_custody_archive_verifications=evidence_bundle_retention_custody_archive_verifications,
        latest_evidence_bundle_retention_custody_archive_verification=latest_evidence_bundle_retention_custody_archive_verification,
        evidence_bundle_retention_custody_retrievals=evidence_bundle_retention_custody_retrievals,
        latest_evidence_bundle_retention_custody_retrieval=latest_evidence_bundle_retention_custody_retrieval,
        evidence_bundle_retention_custody_retrieval_verifications=evidence_bundle_retention_custody_retrieval_verifications,
        latest_evidence_bundle_retention_custody_retrieval_verification=latest_evidence_bundle_retention_custody_retrieval_verification,
        evidence_bundle_retention_custody_returns=evidence_bundle_retention_custody_returns,
        latest_evidence_bundle_retention_custody_return=latest_evidence_bundle_retention_custody_return,
        evidence_bundle_retention_custody_return_verifications=evidence_bundle_retention_custody_return_verifications,
        latest_evidence_bundle_retention_custody_return_verification=latest_evidence_bundle_retention_custody_return_verification,
        evidence_bundle_retention_custody_redeposits=evidence_bundle_retention_custody_redeposits,
        latest_evidence_bundle_retention_custody_redeposit=latest_evidence_bundle_retention_custody_redeposit,
        evidence_bundle_retention_custody_redeposit_verifications=evidence_bundle_retention_custody_redeposit_verifications,
        latest_evidence_bundle_retention_custody_redeposit_verification=latest_evidence_bundle_retention_custody_redeposit_verification,
        evidence_bundle_retention_custody_inventories=evidence_bundle_retention_custody_inventories,
        latest_evidence_bundle_retention_custody_inventory=latest_evidence_bundle_retention_custody_inventory,
        evidence_bundle_retention_custody_inventory_verifications=evidence_bundle_retention_custody_inventory_verifications,
        latest_evidence_bundle_retention_custody_inventory_verification=latest_evidence_bundle_retention_custody_inventory_verification,
        evidence_bundle_retention_custody_reconciliations=evidence_bundle_retention_custody_reconciliations,
        latest_evidence_bundle_retention_custody_reconciliation=latest_evidence_bundle_retention_custody_reconciliation,
        evidence_bundle_retention_custody_reconciliation_verifications=evidence_bundle_retention_custody_reconciliation_verifications,
        latest_evidence_bundle_retention_custody_reconciliation_verification=latest_evidence_bundle_retention_custody_reconciliation_verification,
        evidence_bundle_retention_custody_certifications=evidence_bundle_retention_custody_certifications,
        latest_evidence_bundle_retention_custody_certification=latest_evidence_bundle_retention_custody_certification,
        evidence_bundle_retention_custody_certification_verifications=evidence_bundle_retention_custody_certification_verifications,
        latest_evidence_bundle_retention_custody_certification_verification=latest_evidence_bundle_retention_custody_certification_verification,
        evidence_bundle_retention_custody_attestations=evidence_bundle_retention_custody_attestations,
        latest_evidence_bundle_retention_custody_attestation=latest_evidence_bundle_retention_custody_attestation,
        evidence_bundle_retention_custody_attestation_verifications=evidence_bundle_retention_custody_attestation_verifications,
        latest_evidence_bundle_retention_custody_attestation_verification=latest_evidence_bundle_retention_custody_attestation_verification,
        recommended_actions=actions,
    )
    return payload.model_dump(mode="json")


__all__ = ["build_ui_paper_execution_cockpit_payload"]
