"""Paper execution intent selection artifacts (paper-only, CLI-authored)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent
from strategy_validator.contracts.paper_execution import PaperExecutionIntentPreview, PaperExecutionIntentSelectionArtifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _paper_broker_root(output_root: Path | None = None) -> Path:
    if output_root is not None:
        return output_root.resolve()
    return (Path.cwd() / "artifacts" / "paper_broker").resolve()


def _safe_timestamp(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _intent_preview_from_broker_intent(
    intent: PaperBrokerOrderIntent,
    *,
    strategy_id: str | None = None,
    source: str = "operator_cli_selection",
    rationale: str = "Operator-selected paper execution intent for dry-run preparation only.",
    warnings: list[str] | None = None,
) -> PaperExecutionIntentPreview:
    return PaperExecutionIntentPreview(
        tracking_id=intent.tracking_id,
        strategy_id=strategy_id,
        symbol=intent.symbol.upper(),
        side=intent.side,
        qty=float(intent.qty),
        order_type=intent.order_type,
        time_in_force=intent.time_in_force,
        source=source,
        rationale=rationale,
        confidence="MEDIUM",
        warnings=sorted(set(warnings or [])),
    )


def build_paper_execution_intent_selection_artifact(
    intent: PaperBrokerOrderIntent,
    *,
    strategy_id: str | None = None,
    selected_by: str = "operator",
    selection_reason: str = "manual paper dry-run preparation",
    source_artifact_path: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionIntentSelectionArtifact:
    """Build a durable selected-intent artifact without submitting or dry-running an order."""

    now = generated_at_utc or datetime.now(timezone.utc)
    preview = _intent_preview_from_broker_intent(
        intent,
        strategy_id=strategy_id,
        warnings=["OPERATOR_SELECTED_INTENT_REQUIRES_DRY_RUN_ARTIFACT"],
    )
    dry_cmd = (
        "strategy-validator-paper-broker dry-run-order "
        f"--tracking-id {intent.tracking_id} --symbol {intent.symbol.upper()} "
        f"--side {intent.side} --qty {float(intent.qty):g}"
    )
    artifact = PaperExecutionIntentSelectionArtifact(
        generated_at_utc=now,
        tracking_id=intent.tracking_id,
        strategy_id=strategy_id,
        selected_by=selected_by.strip() or "operator",
        selection_reason=selection_reason.strip() or "manual paper dry-run preparation",
        source_artifact_path=source_artifact_path,
        selected_intent=preview,
        broker_intent=intent.model_dump(mode="json"),
        dry_run_command_hint=dry_cmd,
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_execution_intent_selection_artifact(
    intent: PaperBrokerOrderIntent,
    *,
    strategy_id: str | None = None,
    selected_by: str = "operator",
    selection_reason: str = "manual paper dry-run preparation",
    source_artifact_path: str | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionIntentSelectionArtifact]:
    """Write latest + immutable history selected-intent artifacts."""

    artifact = build_paper_execution_intent_selection_artifact(
        intent,
        strategy_id=strategy_id,
        selected_by=selected_by,
        selection_reason=selection_reason,
        source_artifact_path=source_artifact_path,
        generated_at_utc=generated_at_utc,
    )
    broker_root = _paper_broker_root(output_root)
    tracking_dir = broker_root / intent.tracking_id
    history_dir = tracking_dir / "intent_selections"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = tracking_dir / "paper_execution_intent_selection.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def read_paper_execution_intent_selection_artifact(
    *,
    tracking_id: str | None = None,
    selection_artifact_path: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None]:
    """Read one selected-intent artifact for exact dry-run replay.

    When ``selection_artifact_path`` is provided it is authoritative. Otherwise
    ``tracking_id`` resolves to the latest pointer under the paper-broker root.
    The returned payload includes ``artifact_path`` for downstream evidence links.
    """

    if selection_artifact_path is not None:
        path = selection_artifact_path.expanduser().resolve()
    else:
        tid = (tracking_id or "").strip()
        if not tid:
            return None, None
        path = _paper_broker_root(output_root) / tid / "paper_execution_intent_selection.json"
    raw = _safe_read_json(path)
    if raw is None:
        return path, None
    raw = {**raw, "artifact_path": str(path)}
    return path, raw


def read_latest_paper_execution_intent_selection(*, repo_root: Path | None = None) -> tuple[Path | None, dict[str, Any] | None, int]:
    """Return the newest selected-intent artifact across paper-broker tracking dirs."""

    from strategy_validator.application.research_os_paths import artifact_root_directory

    root = artifact_root_directory(repo_root) / "paper_broker"
    if not root.is_dir():
        return None, None, 0

    def _mtime(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    history_paths = list(root.glob("*/intent_selections/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in history_paths if path.parent.parent.name}
    latest_paths = [p for p in root.glob("*/paper_execution_intent_selection.json") if p.parent.name not in history_tracking_ids]
    paths = history_paths + latest_paths
    if not paths:
        return None, None, 0
    for path in sorted(paths, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is not None:
            raw = {**raw, "artifact_path": str(path)}
            return path, raw, len(paths)
    return None, None, len(paths)


__all__ = [
    "build_paper_execution_intent_selection_artifact",
    "read_latest_paper_execution_intent_selection",
    "read_paper_execution_intent_selection_artifact",
    "write_paper_execution_intent_selection_artifact",
]
