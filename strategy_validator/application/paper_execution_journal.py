"""Durable paper execution evidence writers (paper-only; no network/order authority)."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent, PaperBrokerOrderResult
from strategy_validator.contracts.paper_execution import PaperExecutionDryRunArtifact
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _paper_broker_root(output_root: Path | None = None) -> Path:
    root = output_root if output_root is not None else Path.cwd() / "artifacts" / "paper_broker"
    return root.expanduser().resolve()


def _safe_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def build_paper_order_dry_run_artifact(
    intent: PaperBrokerOrderIntent,
    result: PaperBrokerOrderResult,
    *,
    generated_at_utc: datetime | None = None,
    source_selection_artifact_path: str | None = None,
    source_selection_artifact_sha256: str | None = None,
) -> PaperExecutionDryRunArtifact:
    """Build a redacted, durable dry-run artifact without submitting an order."""

    now = generated_at_utc or datetime.now(timezone.utc)
    replayed = bool((source_selection_artifact_sha256 or "").strip())
    artifact = PaperExecutionDryRunArtifact(
        generated_at_utc=now,
        tracking_id=intent.tracking_id,
        intent=intent.model_dump(mode="json"),
        result=result.model_dump(mode="json"),
        source_selection_artifact_path=(source_selection_artifact_path or None),
        source_selection_artifact_sha256=(source_selection_artifact_sha256 or None),
        replayed_from_selected_intent=replayed,
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_order_dry_run_artifact(
    intent: PaperBrokerOrderIntent,
    result: PaperBrokerOrderResult,
    *,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
    source_selection_artifact_path: str | None = None,
    source_selection_artifact_sha256: str | None = None,
) -> tuple[Path, Path, PaperExecutionDryRunArtifact]:
    """Write latest + immutable-history dry-run artifacts for cockpit/journal consumption."""

    artifact = build_paper_order_dry_run_artifact(
        intent,
        result,
        generated_at_utc=generated_at_utc,
        source_selection_artifact_path=source_selection_artifact_path,
        source_selection_artifact_sha256=source_selection_artifact_sha256,
    )
    broker_root = _paper_broker_root(output_root)
    tracking_dir = broker_root / intent.tracking_id
    history_dir = tracking_dir / "dry_runs"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = tracking_dir / "paper_order_dry_run.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


__all__ = [
    "build_paper_order_dry_run_artifact",
    "write_paper_order_dry_run_artifact",
]
