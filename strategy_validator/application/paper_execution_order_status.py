"""Paper broker order-status refresh artifacts.

The refresh path is CLI evidence only. It fetches or records broker order status
for an existing guarded paper submission; it never submits a new order and never
exposes secrets to UI routes.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.paper_broker import PaperBrokerOrderResult
from strategy_validator.contracts.paper_execution import PaperExecutionOrderStatusArtifact, PaperExecutionOrderStatusView
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def _paper_broker_root(*, repo_root: Path | None = None, output_root: Path | None = None) -> Path:
    if output_root is not None:
        return output_root.expanduser().resolve()
    return (artifact_root_directory(repo_root) / "paper_broker").resolve()


def _safe_timestamp(now: datetime) -> str:
    return now.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")


def _safe_read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _strings(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(x) for x in value if x not in (None, "")]
    if value in (None, ""):
        return []
    return [str(value)]


def find_latest_submission_artifact(
    *,
    tracking_id: str | None = None,
    submission_artifact_path: Path | None = None,
    output_root: Path | None = None,
    repo_root: Path | None = None,
) -> tuple[Path | None, dict[str, Any] | None, str | None]:
    """Find the latest guarded paper submission artifact."""

    if submission_artifact_path is not None:
        raw = _safe_read_json(submission_artifact_path)
        digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw)) if raw else None
        return submission_artifact_path, raw, digest

    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    candidates: list[Path] = []
    if tracking_id:
        base = root / tracking_id
        candidates.extend(base.glob("submissions/*.json"))
        candidates.append(base / "paper_order_submission.json")
    else:
        candidates.extend(root.glob("*/submissions/*.json"))
        candidates.extend(root.glob("*/paper_order_submission.json"))
    for path in sorted({p for p in candidates if p.exists()}, key=_mtime, reverse=True):
        raw = _safe_read_json(path)
        if raw is None:
            continue
        digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
        return path, raw, digest
    return None, None, None


def broker_order_id_from_submission(raw: dict[str, Any] | None) -> str | None:
    if not raw:
        return None
    result = _as_dict(raw.get("result")) if raw.get("schema_version") == "paper_execution_submission_artifact/v1" else raw
    value = result.get("broker_order_id") or result.get("id") or _as_dict(result.get("evidence_redacted")).get("id")
    return str(value).strip() if value not in (None, "") else None


def tracking_id_from_submission(path: Path | None, raw: dict[str, Any] | None) -> str | None:
    if raw and raw.get("tracking_id"):
        return str(raw.get("tracking_id"))
    if path is None:
        return None
    if path.parent.name == "submissions":
        return path.parent.parent.name
    return path.parent.name


def build_paper_order_status_artifact(
    *,
    tracking_id: str,
    broker_order_id: str,
    result: PaperBrokerOrderResult,
    source_submission_artifact_path: str | None = None,
    source_submission_artifact_sha256: str | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionOrderStatusArtifact:
    now = generated_at_utc or datetime.now(timezone.utc)
    artifact = PaperExecutionOrderStatusArtifact(
        generated_at_utc=now,
        tracking_id=tracking_id,
        broker_order_id=broker_order_id,
        source_submission_artifact_path=source_submission_artifact_path,
        source_submission_artifact_sha256=source_submission_artifact_sha256,
        result=result.model_dump(mode="json"),
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_order_status_artifact(
    *,
    tracking_id: str,
    broker_order_id: str,
    result: PaperBrokerOrderResult,
    source_submission_artifact_path: str | None = None,
    source_submission_artifact_sha256: str | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionOrderStatusArtifact]:
    artifact = build_paper_order_status_artifact(
        tracking_id=tracking_id,
        broker_order_id=broker_order_id,
        result=result,
        source_submission_artifact_path=source_submission_artifact_path,
        source_submission_artifact_sha256=source_submission_artifact_sha256,
        generated_at_utc=generated_at_utc,
    )
    root = _paper_broker_root(output_root=output_root) / tracking_id
    history_dir = root / "order_statuses"
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = root / "paper_order_status.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def read_paper_order_status_views(*, repo_root: Path | None = None, output_root: Path | None = None, limit: int = 100) -> list[PaperExecutionOrderStatusView]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    if not root.is_dir():
        return []
    candidates = list(root.glob("*/order_statuses/*.json"))
    history_tracking_ids = {path.parent.parent.name for path in candidates if path.parent.parent.name}
    for latest_path in root.glob("*/paper_order_status.json"):
        if latest_path.parent.name not in history_tracking_ids:
            candidates.append(latest_path)
    rows: list[PaperExecutionOrderStatusView] = []
    for path in sorted(candidates, key=_mtime, reverse=True)[:limit]:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        result = _as_dict(raw.get("result"))
        evidence = _as_dict(result.get("evidence_redacted"))
        digest = str(raw.get("artifact_sha256") or canonical_json_sha256(raw))
        try:
            filled = float(result.get("filled_qty")) if result.get("filled_qty") is not None else None
        except (TypeError, ValueError):
            filled = None
        rows.append(
            PaperExecutionOrderStatusView(
                tracking_id=str(raw.get("tracking_id") or path.parent.parent.name if path.parent.name == "order_statuses" else path.parent.name),
                artifact_path=str(path),
                artifact_sha256=digest,
                generated_at_utc=str(raw.get("generated_at_utc") or result.get("retrieved_at_utc") or "") or None,
                broker_order_id=str(raw.get("broker_order_id") or result.get("broker_order_id") or evidence.get("id") or "") or None,
                status=str(result.get("status") or evidence.get("status") or "") or None,
                ok=bool(result.get("ok")) if result.get("ok") is not None else None,
                filled_qty=filled,
                symbol=str(evidence.get("symbol") or "").upper() or None,
                side=str(evidence.get("side") or "").lower() or None,
                policy_status=str(result.get("policy_status") or "") or None,
                source_submission_artifact_sha256=str(raw.get("source_submission_artifact_sha256") or "") or None,
                source_submission_artifact_path=str(raw.get("source_submission_artifact_path") or "") or None,
                warnings=_strings(result.get("warnings")),
                blockers=_strings(result.get("blockers")),
            )
        )
    return sorted(rows, key=lambda row: row.generated_at_utc or "", reverse=True)[:limit]


__all__ = [
    "broker_order_id_from_submission",
    "build_paper_order_status_artifact",
    "find_latest_submission_artifact",
    "read_paper_order_status_views",
    "tracking_id_from_submission",
    "write_paper_order_status_artifact",
]
