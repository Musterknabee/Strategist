"""Intent-preview helpers for the paper execution cockpit read model."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from strategy_validator.application.paper_execution_cockpit_execution_common import _as_dict, _safe_read_json
from strategy_validator.application.paper_execution_cockpit_runtime import *  # noqa: F403,F401

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

__all__ = [
    "_broker_status",
    "_build_intent_preview",
    "_dry_run",
    "_intent_selection_count",
    "_selected_artifact_to_preview",
    "_selection_artifact",
]
