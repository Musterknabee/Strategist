"""Paper-only Shadow Book operations (artifact-backed; no broker/order authority)."""
from __future__ import annotations

import json
import shutil
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory
from strategy_validator.contracts.shadow_book import (
    ShadowBook,
    ShadowBookAllocation,
    ShadowBookDailySnapshot,
    ShadowBookEvent,
    ShadowBookFill,
    ShadowBookPosition,
    ShadowBookRiskSummary,
    ShadowBookStatus,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def shadow_book_root(repo_root: Path | None = None) -> Path:
    return (artifact_root_directory(repo_root) / "shadow_books").resolve()


def _book_dir(book_id: str, *, repo_root: Path | None = None) -> Path:
    clean = book_id.strip()
    if not clean or Path(clean).name != clean or ".." in clean:
        raise ValueError("INVALID_BOOK_ID")
    return (shadow_book_root(repo_root) / clean).resolve()


def _latest_dir(repo_root: Path | None = None) -> Path:
    return (shadow_book_root(repo_root) / "latest").resolve()


def _json_default(o: Any) -> str:
    if hasattr(o, "isoformat"):
        return o.isoformat()
    raise TypeError(type(o))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _finalize_book(book: ShadowBook) -> ShadowBook:
    body = book.model_dump(mode="json", exclude={"manifest_sha256"})
    return book.model_copy(update={"manifest_sha256": canonical_json_sha256(body)})


def _finalize_snapshot(snapshot: ShadowBookDailySnapshot) -> ShadowBookDailySnapshot:
    body = snapshot.model_dump(mode="json", exclude={"snapshot_sha256"})
    return snapshot.model_copy(update={"snapshot_sha256": canonical_json_sha256(body)})


def _finalize_risk(risk: ShadowBookRiskSummary) -> ShadowBookRiskSummary:
    body = risk.model_dump(mode="json", exclude={"risk_sha256"})
    return risk.model_copy(update={"risk_sha256": canonical_json_sha256(body)})


def _finalize_event(event: ShadowBookEvent) -> ShadowBookEvent:
    body = event.model_dump(mode="json", exclude={"event_sha256"})
    return event.model_copy(update={"event_sha256": canonical_json_sha256(body)})


def _write_book(book: ShadowBook, *, repo_root: Path | None = None) -> ShadowBook:
    b = _finalize_book(book)
    bdir = _book_dir(b.book_id, repo_root=repo_root)
    _write_json(bdir / "shadow_book_manifest.json", b.model_dump(mode="json"))
    latest = _latest_dir(repo_root)
    latest.mkdir(parents=True, exist_ok=True)
    _write_json(latest / "shadow_book_manifest.json", b.model_dump(mode="json"))
    _write_json(latest / "latest_ref.json", {"book_id": b.book_id, "manifest_path": str((bdir / "shadow_book_manifest.json").resolve())})
    return b


def load_shadow_book(book_id: str, *, repo_root: Path | None = None) -> ShadowBook:
    path = _book_dir(book_id, repo_root=repo_root) / "shadow_book_manifest.json"
    return ShadowBook.model_validate(_read_json(path))


def create_shadow_book(
    *,
    book_id: str,
    starting_capital: float = 100_000.0,
    allocations: list[ShadowBookAllocation] | None = None,
    overwrite: bool = False,
    repo_root: Path | None = None,
) -> ShadowBook:
    bdir = _book_dir(book_id, repo_root=repo_root)
    if bdir.exists():
        if not overwrite:
            raise FileExistsError(f"SHADOW_BOOK_EXISTS:{book_id}")
        shutil.rmtree(bdir)
    bdir.mkdir(parents=True, exist_ok=True)
    for sub in ("allocations", "fills", "daily_snapshots", "risk_summaries", "events"):
        (bdir / sub).mkdir(parents=True, exist_ok=True)
    book = ShadowBook(
        book_id=book_id,
        starting_capital=float(starting_capital),
        cash=float(starting_capital),
        allocations=allocations or [],
        warnings=["PAPER_ONLY_SHADOW_BOOK", "NO_BROKER_ORDERS"],
    )
    event = _finalize_event(
        ShadowBookEvent(
            event_id=f"{book_id}-created",
            book_id=book_id,
            event_type="CREATED",
            message="Paper-only shadow book created; no broker order authority.",
        )
    )
    _write_json(bdir / "events" / f"{event.event_id}.json", event.model_dump(mode="json"))
    return _write_book(book.model_copy(update={"event_count": 1}), repo_root=repo_root)


def _load_prices(price_path: Path | None, *, default_price: float = 100.0) -> dict[str, float]:
    if price_path is None or not price_path.is_file():
        return {"DEFAULT": float(default_price)}
    raw = json.loads(price_path.read_text(encoding="utf-8")) if price_path.suffix.lower() == ".json" else None
    if isinstance(raw, dict):
        prices = raw.get("prices", raw)
        if isinstance(prices, dict):
            return {str(k).upper(): float(v) for k, v in prices.items()}
    raise ValueError("UNSUPPORTED_PRICE_FIXTURE")


def apply_allocation_result(book_id: str, allocation_path: Path, *, repo_root: Path | None = None) -> ShadowBook:
    book = load_shadow_book(book_id, repo_root=repo_root)
    raw = _read_json(allocation_path)
    rows = raw.get("allocations") if isinstance(raw.get("allocations"), list) else raw.get("strategy_allocations")
    if not isinstance(rows, list):
        raise ValueError("ALLOCATION_ARTIFACT_MISSING_ALLOCATIONS")
    allocations: list[ShadowBookAllocation] = []
    for i, item in enumerate(rows):
        if not isinstance(item, dict):
            continue
        sid = str(item.get("strategy_id") or item.get("id") or f"strategy-{i}")
        w = float(item.get("target_weight", item.get("weight", 0.0)))
        allocations.append(
            ShadowBookAllocation(
                strategy_id=sid,
                target_weight=w,
                notional=float(book.starting_capital) * w,
                source=str(allocation_path),
                evidence_refs=[{"artifact_path": str(allocation_path.resolve())}],
            )
        )
    bdir = _book_dir(book_id, repo_root=repo_root)
    _write_json(bdir / "allocations" / "allocation_result.json", raw)
    return _write_book(book.model_copy(update={"allocations": allocations}), repo_root=repo_root)


def simulate_daily_fills(
    book_id: str,
    *,
    as_of_date: date,
    price_fixture: Path | None = None,
    repo_root: Path | None = None,
) -> list[ShadowBookFill]:
    book = load_shadow_book(book_id, repo_root=repo_root)
    prices = _load_prices(price_fixture)
    fills: list[ShadowBookFill] = []
    ts = datetime.combine(as_of_date, datetime.min.time(), tzinfo=timezone.utc)
    for alloc in book.allocations:
        if "synthetic" in alloc.strategy_id.lower():
            continue
        symbol = alloc.strategy_id.split("-")[-1].upper() if "-" in alloc.strategy_id else "SPY"
        price = prices.get(symbol, prices.get("DEFAULT", 100.0))
        qty = 0.0 if price <= 0 else alloc.notional / price
        side = "BUY" if qty >= 0 else "SELL"
        fill = ShadowBookFill(
            fill_id=canonical_json_sha256({"book_id": book_id, "date": as_of_date.isoformat(), "strategy_id": alloc.strategy_id})[:24],
            strategy_id=alloc.strategy_id,
            symbol=symbol,
            timestamp_utc=ts,
            side=side,  # type: ignore[arg-type]
            quantity=abs(qty),
            price=price,
            notional=abs(qty) * price,
        )
        fills.append(fill)
    bdir = _book_dir(book_id, repo_root=repo_root)
    _write_json(bdir / "fills" / f"{as_of_date.isoformat()}.json", [f.model_dump(mode="json") for f in fills])
    return fills


def compute_risk_summary(
    book_id: str,
    *,
    as_of_date: date,
    positions: list[ShadowBookPosition],
    cash: float,
    previous_equity_peak: float | None = None,
    max_gross_exposure: float = 1.0,
    max_single_strategy_weight: float = 0.40,
    max_drawdown: float = 0.20,
    repo_root: Path | None = None,
) -> ShadowBookRiskSummary:
    gross = sum(abs(p.market_value) for p in positions)
    nlv = cash + sum(p.market_value for p in positions)
    denom = max(abs(nlv), 1e-9)
    single = max((abs(p.market_value) / denom for p in positions), default=0.0)
    peak = max(previous_equity_peak or nlv, nlv)
    dd = 0.0 if peak <= 0 else max(0.0, (peak - nlv) / peak)
    flags: list[str] = []
    blockers: list[str] = []
    warnings: list[str] = []
    if gross / denom > max_gross_exposure:
        flags.append("MAX_GROSS_EXPOSURE_EXCEEDED")
        blockers.append("MAX_GROSS_EXPOSURE_EXCEEDED")
    if single > max_single_strategy_weight:
        flags.append("MAX_SINGLE_STRATEGY_WEIGHT_EXCEEDED")
        warnings.append("MAX_SINGLE_STRATEGY_WEIGHT_EXCEEDED")
    if dd > max_drawdown:
        flags.append("MAX_DRAWDOWN_EXCEEDED")
        blockers.append("MAX_DRAWDOWN_EXCEEDED")
    status = ShadowBookStatus.FROZEN_BY_RULE if blockers else ShadowBookStatus.ACTIVE
    risk = _finalize_risk(
        ShadowBookRiskSummary(
            book_id=book_id,
            as_of_date=as_of_date,
            status=status,
            gross_exposure=gross,
            net_liquidation_value=nlv,
            cash=cash,
            max_single_strategy_weight=single,
            max_drawdown=dd,
            correlated_cluster_exposure=gross / denom,
            risk_flags=flags,
            warnings=warnings,
            blockers=blockers,
        )
    )
    bdir = _book_dir(book_id, repo_root=repo_root)
    _write_json(bdir / "risk_summaries" / f"{as_of_date.isoformat()}.json", risk.model_dump(mode="json"))
    return risk


def mark_to_market(
    book_id: str,
    *,
    as_of_date: date,
    price_fixture: Path | None = None,
    repo_root: Path | None = None,
) -> ShadowBookDailySnapshot:
    book = load_shadow_book(book_id, repo_root=repo_root)
    prices = _load_prices(price_fixture)
    fills_path = _book_dir(book_id, repo_root=repo_root) / "fills" / f"{as_of_date.isoformat()}.json"
    fills_raw = json.loads(fills_path.read_text(encoding="utf-8")) if fills_path.is_file() else []
    fills = [ShadowBookFill.model_validate(x) for x in fills_raw]
    positions: list[ShadowBookPosition] = []
    spent = 0.0
    for fill in fills:
        last = prices.get(fill.symbol.upper(), fill.price)
        mv = fill.quantity * last
        spent += fill.quantity * fill.price
        positions.append(
            ShadowBookPosition(
                strategy_id=fill.strategy_id,
                symbol=fill.symbol,
                quantity=fill.quantity,
                avg_price=fill.price,
                last_price=last,
                market_value=mv,
                unrealized_pnl=(last - fill.price) * fill.quantity,
            )
        )
    cash = book.starting_capital - spent
    total_mv = sum(p.market_value for p in positions)
    nlv = cash + total_mv
    weighted = [p.model_copy(update={"weight": 0.0 if nlv == 0 else p.market_value / nlv}) for p in positions]
    risk = compute_risk_summary(book_id, as_of_date=as_of_date, positions=weighted, cash=cash, repo_root=repo_root)
    snapshot = _finalize_snapshot(
        ShadowBookDailySnapshot(
            book_id=book_id,
            as_of_date=as_of_date,
            status=risk.status,
            positions=weighted,
            cash=cash,
            net_liquidation_value=nlv,
            daily_pnl=nlv - book.starting_capital,
            cumulative_pnl=nlv - book.starting_capital,
            drawdown=risk.max_drawdown,
            risk_summary=risk,
        )
    )
    bdir = _book_dir(book_id, repo_root=repo_root)
    snap_path = bdir / "daily_snapshots" / f"{as_of_date.isoformat()}.json"
    _write_json(snap_path, snapshot.model_dump(mode="json"))
    status = risk.status if risk.status == ShadowBookStatus.FROZEN_BY_RULE else book.status
    updated = book.model_copy(
        update={
            "status": status,
            "cash": cash,
            "latest_snapshot_path": str(snap_path.resolve()),
            "latest_risk_summary_path": str((bdir / "risk_summaries" / f"{as_of_date.isoformat()}.json").resolve()),
            "blockers": sorted(set([*book.blockers, *risk.blockers])),
            "warnings": sorted(set([*book.warnings, *risk.warnings])),
        }
    )
    _write_book(updated, repo_root=repo_root)
    latest = _latest_dir(repo_root)
    _write_json(latest / "latest_daily_snapshot.json", snapshot.model_dump(mode="json"))
    _write_json(latest / "latest_risk_summary.json", risk.model_dump(mode="json"))
    return snapshot


def apply_risk_limits(book_id: str, *, repo_root: Path | None = None) -> ShadowBookRiskSummary | None:
    book = load_shadow_book(book_id, repo_root=repo_root)
    if not book.latest_risk_summary_path:
        return None
    return ShadowBookRiskSummary.model_validate(_read_json(Path(book.latest_risk_summary_path)))


def freeze_shadow_book(book_id: str, *, reason: str, repo_root: Path | None = None) -> ShadowBook:
    book = load_shadow_book(book_id, repo_root=repo_root)
    updated = book.model_copy(update={"status": ShadowBookStatus.FROZEN_BY_RULE, "blockers": sorted(set([*book.blockers, reason]))})
    return _write_book(updated, repo_root=repo_root)


def build_ui_shadow_book_latest_payload(*, repo_root: Path | None = None) -> dict[str, Any]:
    latest = _latest_dir(repo_root)
    manifest = latest / "shadow_book_manifest.json"
    degraded: list[str] = []
    if not manifest.is_file():
        return {
            "schema_version": "ui_shadow_book/v1",
            "generated_at_utc": datetime.now(timezone.utc).isoformat(),
            "read_plane_only": True,
            "no_live_trading": True,
            "no_order_controls": True,
            "scan_root": str(shadow_book_root(repo_root)),
            "latest": None,
            "latest_snapshot": None,
            "latest_risk_summary": None,
            "degraded": ["NO_SHADOW_BOOK_ARTIFACT"],
        }
    latest_payload = _read_json(manifest)
    snap_path = latest / "latest_daily_snapshot.json"
    risk_path = latest / "latest_risk_summary.json"
    snapshot = _read_json(snap_path) if snap_path.is_file() else None
    risk = _read_json(risk_path) if risk_path.is_file() else None
    if snapshot is None:
        degraded.append("NO_SHADOW_BOOK_DAILY_SNAPSHOT")
    if risk is None:
        degraded.append("NO_SHADOW_BOOK_RISK_SUMMARY")
    return {
        "schema_version": "ui_shadow_book/v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "read_plane_only": True,
        "no_live_trading": True,
        "no_order_controls": True,
        "scan_root": str(shadow_book_root(repo_root)),
        "latest": latest_payload,
        "latest_snapshot": snapshot,
        "latest_risk_summary": risk,
        "degraded": degraded,
    }


__all__ = [
    "apply_allocation_result",
    "apply_risk_limits",
    "build_ui_shadow_book_latest_payload",
    "compute_risk_summary",
    "create_shadow_book",
    "freeze_shadow_book",
    "load_shadow_book",
    "mark_to_market",
    "shadow_book_root",
    "simulate_daily_fills",
]
