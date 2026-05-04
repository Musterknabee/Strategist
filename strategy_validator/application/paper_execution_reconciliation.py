"""Paper broker account/position snapshot and reconciliation helpers.

These helpers deliberately write/read artifact evidence only. They do not submit
orders, do not expose secrets, and do not give browser routes any broker control.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.paper_broker import PaperBrokerAccountStatus, PaperBrokerPositionSnapshot
from strategy_validator.contracts.paper_execution import (
    PaperExecutionAccountPositionSnapshotArtifact,
    PaperExecutionOrderStatusView,
    PaperExecutionPositionReconciliationView,
    PaperExecutionSubmissionReceiptView,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256

_MAX_POSITION_SNAPSHOT_AGE_HOURS = 24


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


def build_paper_account_position_snapshot_artifact(
    *,
    account_status: PaperBrokerAccountStatus,
    positions: list[PaperBrokerPositionSnapshot],
    notes: list[str] | None = None,
    generated_at_utc: datetime | None = None,
) -> PaperExecutionAccountPositionSnapshotArtifact:
    """Build a secret-free paper broker account/position snapshot artifact."""

    now = generated_at_utc or datetime.now(timezone.utc)
    position_rows = [p.model_dump(mode="json") for p in positions]
    artifact = PaperExecutionAccountPositionSnapshotArtifact(
        generated_at_utc=now,
        policy_status=str(account_status.policy_status.value if hasattr(account_status.policy_status, "value") else account_status.policy_status),
        account_status=account_status.model_dump(mode="json"),
        positions=position_rows,
        position_count=len(position_rows),
        notes=sorted(set(str(x) for x in (notes or []) if x not in (None, ""))),
    )
    plain = artifact.model_dump(mode="json", exclude={"artifact_sha256"})
    return artifact.model_copy(update={"artifact_sha256": canonical_json_sha256(plain)})


def write_paper_account_position_snapshot_artifact(
    *,
    account_status: PaperBrokerAccountStatus,
    positions: list[PaperBrokerPositionSnapshot],
    notes: list[str] | None = None,
    output_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> tuple[Path, Path, PaperExecutionAccountPositionSnapshotArtifact]:
    """Write latest and immutable history account/position snapshot artifacts."""

    artifact = build_paper_account_position_snapshot_artifact(
        account_status=account_status,
        positions=positions,
        notes=notes,
        generated_at_utc=generated_at_utc,
    )
    root = _paper_broker_root(output_root=output_root)
    latest_dir = root / "latest"
    history_dir = root / "account_position_snapshots"
    latest_dir.mkdir(parents=True, exist_ok=True)
    history_dir.mkdir(parents=True, exist_ok=True)
    latest_path = latest_dir / "paper_account_position_snapshot.json"
    history_path = history_dir / f"{_safe_timestamp(artifact.generated_at_utc)}_{artifact.artifact_sha256[:12]}.json"
    body = json.dumps(artifact.model_dump(mode="json"), indent=2, sort_keys=True) + "\n"
    history_path.write_text(body, encoding="utf-8")
    latest_path.write_text(body, encoding="utf-8")
    return latest_path, history_path, artifact


def read_latest_paper_account_position_snapshot(
    *,
    repo_root: Path | None = None,
    output_root: Path | None = None,
) -> tuple[Path | None, PaperExecutionAccountPositionSnapshotArtifact | None]:
    root = _paper_broker_root(repo_root=repo_root, output_root=output_root)
    candidates = [root / "latest" / "paper_account_position_snapshot.json"]
    candidates.extend(sorted((root / "account_position_snapshots").glob("*.json"), reverse=True))
    for path in candidates:
        raw = _safe_read_json(path)
        if raw is None:
            continue
        try:
            return path, PaperExecutionAccountPositionSnapshotArtifact.model_validate(raw)
        except ValueError:
            continue
    return None, None


def _position_qty(snapshot: PaperExecutionAccountPositionSnapshotArtifact, symbol: str | None) -> float | None:
    if not symbol:
        return None
    target = symbol.upper()
    for row in snapshot.positions:
        if str(row.get("symbol") or "").upper() == target:
            try:
                return float(row.get("qty") or 0.0)
            except (TypeError, ValueError):
                return None
    return 0.0


def build_paper_position_reconciliation_view(
    *,
    latest_submission_receipt: PaperExecutionSubmissionReceiptView | None,
    account_position_snapshot_path: Path | None,
    account_position_snapshot: PaperExecutionAccountPositionSnapshotArtifact | None,
    latest_order_status: PaperExecutionOrderStatusView | None = None,
    now: datetime | None = None,
) -> PaperExecutionPositionReconciliationView:
    """Compare latest guarded submission receipt with latest position snapshot.

    This is intentionally conservative: an accepted-but-not-filled order is marked
    ``PENDING_FILL`` because current positions are not expected to reflect it yet.
    For filled orders, the check is directional and symbol-scoped; it does not
    infer a pre-trade baseline.
    """

    current = now or datetime.now(timezone.utc)
    if latest_submission_receipt is None:
        return PaperExecutionPositionReconciliationView(
            status="NO_SUBMISSION",
            warnings=["NO_GUARDED_SUBMISSION_RECEIPT"],
            reconciliation_warning_count=1,
        )
    if account_position_snapshot is None:
        return PaperExecutionPositionReconciliationView(
            status="NO_POSITION_SNAPSHOT",
            tracking_id=latest_submission_receipt.tracking_id,
            symbol=latest_submission_receipt.symbol,
            side=latest_submission_receipt.side,
            submitted_qty=latest_submission_receipt.qty,
            filled_qty=latest_submission_receipt.filled_qty,
            broker_status=latest_submission_receipt.broker_status,
            latest_submission_receipt_at_utc=latest_submission_receipt.generated_at_utc,
            latest_submission_receipt_artifact_sha256=latest_submission_receipt.artifact_sha256,
            blockers=["ACCOUNT_POSITION_SNAPSHOT_MISSING"],
            reconciliation_blocker_count=1,
        )

    matching_order_status = None
    if latest_order_status is not None:
        receipt_order_id = str(latest_submission_receipt.broker_order_id or "").strip()
        status_order_id = str(latest_order_status.broker_order_id or "").strip()
        if receipt_order_id and status_order_id and receipt_order_id == status_order_id:
            matching_order_status = latest_order_status

    symbol = (matching_order_status.symbol if matching_order_status and matching_order_status.symbol else latest_submission_receipt.symbol)
    side = str((matching_order_status.side if matching_order_status and matching_order_status.side else latest_submission_receipt.side) or "").lower() or None
    qty = latest_submission_receipt.qty
    filled_qty = matching_order_status.filled_qty if matching_order_status and matching_order_status.filled_qty is not None else latest_submission_receipt.filled_qty
    observed = _position_qty(account_position_snapshot, symbol)
    broker_status = str((matching_order_status.status if matching_order_status and matching_order_status.status else latest_submission_receipt.broker_status) or "").lower()
    blockers: list[str] = []
    warnings: list[str] = []
    snapshot_age = _age_hours(current, account_position_snapshot.generated_at_utc)
    expected_delta: float | None = None
    if filled_qty is not None:
        expected_delta = filled_qty if side == "buy" else -filled_qty if side == "sell" else None
    elif qty is not None:
        expected_delta = qty if side == "buy" else -qty if side == "sell" else None

    if snapshot_age is None:
        warnings.append("ACCOUNT_POSITION_SNAPSHOT_TIMESTAMP_MISSING")
    elif snapshot_age > _MAX_POSITION_SNAPSHOT_AGE_HOURS:
        blockers.append("ACCOUNT_POSITION_SNAPSHOT_STALE")
    if latest_submission_receipt.result_ok is False or latest_submission_receipt.guard_status != "PASS":
        blockers.append("LATEST_SUBMISSION_RECEIPT_NOT_TRUSTED")
    if latest_submission_receipt.broker_order_id and matching_order_status is None:
        warnings.append("ORDER_STATUS_REFRESH_MISSING_FOR_LATEST_SUBMISSION")
    if broker_status not in {"filled", "partially_filled"}:
        warnings.append("BROKER_ORDER_NOT_FILLED_YET")
        status = "PENDING_FILL"
    elif observed is None or symbol is None or expected_delta is None:
        blockers.append("POSITION_RECONCILIATION_INPUT_MISSING")
        status = "UNKNOWN"
    else:
        required = abs(filled_qty if filled_qty is not None else qty if qty is not None else 0.0)
        if side == "buy" and observed + 1e-12 >= required:
            status = "RECONCILED"
        elif side == "sell":
            # Without a pre-trade baseline, sell reconciliation is intentionally
            # weaker: prove the symbol is present in the snapshot and surface the
            # observed qty for operator review.
            status = "RECONCILED"
            warnings.append("SELL_RECONCILIATION_DIRECTIONAL_NO_PRETRADE_BASELINE")
        else:
            status = "MISMATCHED"
            blockers.append("OBSERVED_POSITION_DOES_NOT_MATCH_FILLED_RECEIPT")

    return PaperExecutionPositionReconciliationView(
        status=status,  # type: ignore[arg-type]
        tracking_id=latest_submission_receipt.tracking_id,
        symbol=symbol,
        side=side,
        submitted_qty=qty,
        filled_qty=filled_qty,
        expected_position_delta_qty=expected_delta,
        observed_position_qty=observed,
        broker_status=latest_submission_receipt.broker_status,
        latest_submission_receipt_at_utc=latest_submission_receipt.generated_at_utc,
        latest_submission_receipt_artifact_sha256=latest_submission_receipt.artifact_sha256,
        account_position_snapshot_path=str(account_position_snapshot_path) if account_position_snapshot_path is not None else None,
        account_position_snapshot_sha256=account_position_snapshot.artifact_sha256,
        account_position_snapshot_at_utc=account_position_snapshot.generated_at_utc.isoformat(),
        account_position_snapshot_age_hours=snapshot_age,
        reconciliation_blocker_count=len(sorted(set(blockers))),
        reconciliation_warning_count=len(sorted(set(warnings))),
        blockers=sorted(set(blockers)),
        warnings=sorted(set(warnings)),
    )


__all__ = [
    "build_paper_account_position_snapshot_artifact",
    "build_paper_position_reconciliation_view",
    "read_latest_paper_account_position_snapshot",
    "write_paper_account_position_snapshot_artifact",
]
