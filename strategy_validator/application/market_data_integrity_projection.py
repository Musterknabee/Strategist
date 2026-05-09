"""Read-plane projection for market-data integrity result artifacts.

This surface deliberately reads generated research artifacts only. It never calls
providers, mutates ledgers, submits orders, or upgrades any strategy to live
execution authority.
"""
from __future__ import annotations

import json
import os
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.market_data_integrity import MarketDataIntegrityResult

_SCHEMA_VERSION = "ui_market_data_integrity/v1"
_ARTIFACT_NAME = "market_data_integrity_result.json"
_READ_PLANE_ONLY = True
_MUTATION_AUTHORITY = "none_read_plane"
_EXECUTION_AUTHORITY = "none_read_plane"
_PROMOTION_AUTHORITY = "none_read_plane"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _default_scan_root(repo_root: Path | None = None) -> Path:
    raw = os.environ.get("STRATEGY_VALIDATOR_MARKET_DATA_INTEGRITY_ROOT", "").strip()
    if raw:
        p = Path(raw).expanduser()
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    batch_root = os.environ.get("STRATEGY_VALIDATOR_STRATEGY_BATCH_OUTPUT_ROOT", "").strip()
    if batch_root:
        p = Path(batch_root).expanduser()
        return p if p.is_absolute() else (Path.cwd() / p).resolve()
    art = os.environ.get("STRATEGY_VALIDATOR_ARTIFACT_ROOT", "").strip()
    if art:
        return (Path(art).expanduser().resolve() / "strategy_runs").resolve()
    root = repo_root or Path.cwd()
    return (root / "artifacts" / "strategy_runs").resolve()


def _coerce_scan_root(*, repo_root: Path | None, scan_root: str | Path | None) -> Path:
    if scan_root is not None and str(scan_root).strip():
        p = Path(scan_root).expanduser()
        return p if p.is_absolute() else ((repo_root or Path.cwd()) / p).resolve()
    return _default_scan_root(repo_root)


def _load_result(path: Path) -> tuple[MarketDataIntegrityResult | None, dict[str, Any] | None, str | None]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return None, None, f"INVALID_JSON:{path}:{exc.__class__.__name__}"
    try:
        return MarketDataIntegrityResult.model_validate(raw), raw if isinstance(raw, dict) else None, None
    except ValueError as exc:
        return None, raw if isinstance(raw, dict) else None, f"INVALID_MARKET_DATA_INTEGRITY_RESULT:{path}:{exc.__class__.__name__}"


def _safe_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: Any) -> float | None:
    try:
        if value is None:
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _entry_from_result(path: Path, result: MarketDataIntegrityResult) -> dict[str, Any]:
    coverage = result.trading_calendar_coverage
    return {
        "schema_version": result.schema_version,
        "artifact_path": str(path),
        "artifact_name": path.name,
        "artifact_mtime_utc": datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat(),
        "strategy_id": result.strategy_id,
        "batch_id": result.batch_id,
        "run_id": result.run_id,
        "provider_id": result.provider_id,
        "license_scope": result.license_scope,
        "trust_level": result.trust_level,
        "adjusted_status": result.adjusted_status,
        "as_of_utc": result.as_of_utc.isoformat(),
        "row_count": result.row_count,
        "symbol_count": result.symbol_count,
        "stale_last_bar_hours": result.stale_last_bar_hours,
        "calendar_status": coverage.calendar_status.value,
        "missing_trading_days": coverage.missing_trading_days,
        "missing_date_ratio": coverage.missing_date_ratio,
        "duplicate_vendor_record_count": result.duplicate_vendor_record_count,
        "benchmark_calendar_mismatch": result.benchmark_calendar_mismatch,
        "corporate_action_warning_count": len(result.corporate_action_warnings),
        "survivorship_warning_count": len(result.survivorship_warnings),
        "symbol_continuity_check_count": len(result.symbol_continuity_checks),
        "price_discontinuity_check_count": len(result.price_discontinuity_checks),
        "timezone_session_warning_count": len(result.timezone_session_warnings),
        "gate_status": result.gate_status.value,
        "warning_count": len(result.warnings),
        "blocker_count": len(result.blockers),
        "warnings": list(result.warnings),
        "blockers": list(result.blockers),
        "evidence_sha256": result.evidence_sha256,
        "summary_line": _summary_line(result),
    }


def _summary_line(result: MarketDataIntegrityResult) -> str:
    parts = [
        f"{result.strategy_id}",
        f"gate={result.gate_status.value}",
        f"provider={result.provider_id}",
        f"adjusted={result.adjusted_status}",
        f"rows={result.row_count}",
        f"symbols={result.symbol_count}",
    ]
    if result.stale_last_bar_hours is not None:
        parts.append(f"stale_hours={result.stale_last_bar_hours:.1f}")
    if result.blockers:
        parts.append(f"blockers={len(result.blockers)}")
    elif result.warnings:
        parts.append(f"warnings={len(result.warnings)}")
    return " · ".join(parts)


def _matches(
    entry: dict[str, Any],
    *,
    gate_status: set[str],
    provider_id: str | None,
    adjusted_status: set[str],
    strategy_id_contains: str | None,
    blocker_contains: str | None,
    warning_contains: str | None,
) -> bool:
    if gate_status and str(entry.get("gate_status") or "").upper() not in gate_status:
        return False
    if provider_id and str(entry.get("provider_id") or "") != provider_id:
        return False
    if adjusted_status and str(entry.get("adjusted_status") or "").upper() not in adjusted_status:
        return False
    if strategy_id_contains and strategy_id_contains.lower() not in str(entry.get("strategy_id") or "").lower():
        return False
    if blocker_contains and warning_contains:
        blocker_hay = "\n".join(str(x) for x in entry.get("blockers") or [])
        warning_hay = "\n".join(str(x) for x in entry.get("warnings") or [])
        blocker_hit = blocker_contains.lower() in blocker_hay.lower()
        warning_hit = warning_contains.lower() in warning_hay.lower()
        if blocker_contains.lower() == warning_contains.lower():
            if not (blocker_hit or warning_hit):
                return False
        elif not (blocker_hit and warning_hit):
            return False
    elif blocker_contains:
        hay = "\n".join(str(x) for x in entry.get("blockers") or [])
        if blocker_contains.lower() not in hay.lower():
            return False
    elif warning_contains:
        hay = "\n".join(str(x) for x in entry.get("warnings") or [])
        if warning_contains.lower() not in hay.lower():
            return False
    return True


def _counts(entries: list[dict[str, Any]], key: str) -> dict[str, int]:
    c: Counter[str] = Counter()
    for item in entries:
        value = str(item.get(key) or "UNKNOWN")
        c[value] += 1
    return dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0])))


def _worst_gate(entries: list[dict[str, Any]]) -> str:
    order = {"BLOCKED": 3, "WARNING": 2, "PROVEN": 1, "NOT_APPLICABLE": 0, "UNKNOWN": -1}
    if not entries:
        return "NOT_APPLICABLE"
    return max((str(e.get("gate_status") or "UNKNOWN").upper() for e in entries), key=lambda g: order.get(g, -1))


def build_ui_market_data_integrity_payload(
    *,
    repo_root: str | Path | None = None,
    scan_root: str | Path | None = None,
    gate_status: tuple[str, ...] | list[str] = (),
    provider_id: str | None = None,
    adjusted_status: tuple[str, ...] | list[str] = (),
    strategy_id_contains: str | None = None,
    blocker_contains: str | None = None,
    warning_contains: str | None = None,
    limit: int = 200,
    include_raw: bool = False,
) -> dict[str, Any]:
    """Build the operator market-data integrity projection.

    The projection scans already-generated ``market_data_integrity_result.json``
    artifacts and returns a bounded, UI-safe read model.
    """
    root_path = Path(repo_root).expanduser().resolve() if repo_root else None
    root = _coerce_scan_root(repo_root=root_path, scan_root=scan_root)
    normalized_gate_status = {s.strip().upper() for s in gate_status if str(s).strip()}
    normalized_adjusted_status = {s.strip().upper() for s in adjusted_status if str(s).strip()}
    bounded_limit = max(1, min(int(limit or 200), 1000))
    degraded: list[str] = []
    invalid_artifacts: list[dict[str, str]] = []
    if not root.is_dir():
        degraded.append("SCAN_ROOT_MISSING")
        candidates: list[Path] = []
    else:
        candidates = sorted(root.rglob(_ARTIFACT_NAME), key=lambda p: p.stat().st_mtime, reverse=True)

    all_entries: list[dict[str, Any]] = []
    for path in candidates:
        result, raw, err = _load_result(path)
        if err:
            invalid_artifacts.append({"artifact_path": str(path), "issue_code": err})
            continue
        if result is None:
            invalid_artifacts.append({"artifact_path": str(path), "issue_code": "INVALID_MARKET_DATA_INTEGRITY_RESULT"})
            continue
        entry = _entry_from_result(path, result)
        if include_raw and raw is not None:
            entry["raw_result"] = raw
        all_entries.append(entry)

    if invalid_artifacts:
        degraded.append("INVALID_MARKET_DATA_INTEGRITY_ARTIFACTS")
    filtered = [
        entry
        for entry in all_entries
        if _matches(
            entry,
            gate_status=normalized_gate_status,
            provider_id=provider_id.strip() if provider_id else None,
            adjusted_status=normalized_adjusted_status,
            strategy_id_contains=strategy_id_contains.strip() if strategy_id_contains else None,
            blocker_contains=blocker_contains.strip() if blocker_contains else None,
            warning_contains=warning_contains.strip() if warning_contains else None,
        )
    ]
    returned = filtered[:bounded_limit]
    blocker_count = sum(_safe_int(e.get("blocker_count")) for e in filtered)
    warning_count = sum(_safe_int(e.get("warning_count")) for e in filtered)
    stale_blocked_count = sum(
        1
        for e in filtered
        if any(str(b).startswith("STALE_LAST_BAR_HOURS") for b in e.get("blockers") or [])
    )
    corporate_warning_count = sum(_safe_int(e.get("corporate_action_warning_count")) for e in filtered)
    survivorship_warning_count = sum(_safe_int(e.get("survivorship_warning_count")) for e in filtered)
    duplicate_vendor_record_count = sum(_safe_int(e.get("duplicate_vendor_record_count")) for e in filtered)
    max_stale = max((_safe_float(e.get("stale_last_bar_hours")) or 0.0 for e in filtered), default=None)

    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": _READ_PLANE_ONLY,
        "mutation_authority": _MUTATION_AUTHORITY,
        "promotion_authority": _PROMOTION_AUTHORITY,
        "execution_authority": _EXECUTION_AUTHORITY,
        "no_network_calls": True,
        "no_provider_calls": True,
        "scan_root": str(root),
        "filters": {
            "gate_status": sorted(normalized_gate_status),
            "provider_id": provider_id,
            "adjusted_status": sorted(normalized_adjusted_status),
            "strategy_id_contains": strategy_id_contains,
            "blocker_contains": blocker_contains,
            "warning_contains": warning_contains,
            "limit": bounded_limit,
            "include_raw": include_raw,
        },
        "degraded": degraded,
        "invalid_artifact_count": len(invalid_artifacts),
        "invalid_artifacts": invalid_artifacts[:bounded_limit],
        "artifact_count": len(all_entries),
        "filtered_artifact_count": len(filtered),
        "returned_artifact_count": len(returned),
        "summary": {
            "worst_gate_status": _worst_gate(filtered),
            "blocked_count": sum(1 for e in filtered if str(e.get("gate_status") or "").upper() == "BLOCKED"),
            "warning_gate_count": sum(1 for e in filtered if str(e.get("gate_status") or "").upper() == "WARNING"),
            "proven_count": sum(1 for e in filtered if str(e.get("gate_status") or "").upper() == "PROVEN"),
            "not_applicable_count": sum(1 for e in filtered if str(e.get("gate_status") or "").upper() == "NOT_APPLICABLE"),
            "total_warning_count": warning_count,
            "total_blocker_count": blocker_count,
            "stale_blocked_count": stale_blocked_count,
            "corporate_action_warning_count": corporate_warning_count,
            "survivorship_warning_count": survivorship_warning_count,
            "duplicate_vendor_record_count": duplicate_vendor_record_count,
            "max_stale_last_bar_hours": max_stale,
            "provider_count": len({str(e.get("provider_id") or "UNKNOWN") for e in filtered}),
            "strategy_count": len({str(e.get("strategy_id") or "UNKNOWN") for e in filtered}),
            "run_count": len({str(e.get("run_id") or "UNKNOWN") for e in filtered}),
        },
        "gate_counts": _counts(filtered, "gate_status"),
        "provider_counts": _counts(filtered, "provider_id"),
        "adjusted_status_counts": _counts(filtered, "adjusted_status"),
        "trust_level_counts": _counts(filtered, "trust_level"),
        "latest": returned[0] if returned else None,
        "entries": returned,
        "guardrails": [
            "Read-plane artifact discovery only.",
            "No market-data provider calls are made by this route.",
            "No strategy promotion, order submission, or live-trading authorization is granted.",
            "PROVEN market-data integrity is necessary evidence, not a profitability claim.",
        ],
    }


__all__ = ["build_ui_market_data_integrity_payload"]
