"""Alpaca paper endpoint adapter (optional keys; evidence only)."""
from __future__ import annotations

import base64
import json
from datetime import datetime, timezone
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from strategy_validator.contracts.paper_broker import (
    PaperBrokerAccountStatus,
    PaperBrokerOrderIntent,
    PaperBrokerOrderResult,
    PaperBrokerPolicyStatus,
    PaperBrokerPositionSnapshot,
)

Transport = Callable[[str, dict[str, str], str], tuple[int, bytes]]


def _default_transport(url: str, headers: dict[str, str], method: str = "GET") -> tuple[int, bytes]:
    data = None
    hdrs = dict(headers)
    req = Request(url, data=data, headers=hdrs, method=method)
    with urlopen(req, timeout=30) as resp:  # noqa: S310
        code = int(getattr(resp, "status", 200) or 200)
        return code, resp.read()


def _auth_header(key: str, secret: str) -> str:
    raw = f"{key}:{secret}".encode("utf-8")
    return "Basic " + base64.b64encode(raw).decode("ascii")


def evaluate_alpaca_paper_policy(env: dict[str, str]) -> tuple[PaperBrokerPolicyStatus, list[str], list[str]]:
    warnings: list[str] = []
    blockers: list[str] = []
    mode = (env.get("ALPACA_TRADING_MODE") or "").strip().lower()
    if mode and mode != "paper":
        return PaperBrokerPolicyStatus.BLOCKED_BY_POLICY, warnings, ["ALPACA_TRADING_MODE_MUST_BE_PAPER"]
    live_flag = (env.get("PERSONAL_LIVE_APPROVED") or "").strip().lower()
    if live_flag in ("1", "true", "yes"):
        return PaperBrokerPolicyStatus.BLOCKED_BY_POLICY, warnings, ["PERSONAL_LIVE_APPROVED_MUST_STAY_FALSE"]
    base = (env.get("ALPACA_BASE_URL") or "").strip().lower()
    if base and "paper-api" not in base and "alpaca" in base:
        return PaperBrokerPolicyStatus.BLOCKED_BY_POLICY, warnings, ["ALPACA_BASE_URL_NOT_PAPER_HOST"]
    key = (env.get("ALPACA_API_KEY") or "").strip()
    secret = (env.get("ALPACA_API_SECRET") or "").strip()
    if not key or not secret:
        return PaperBrokerPolicyStatus.PENDING_KEY, warnings, ["ALPACA_KEYS_MISSING"]
    if not base:
        warnings.append("ALPACA_BASE_URL_UNSET_DEFAULTING_PAPER")
    return PaperBrokerPolicyStatus.PAPER_READY, warnings, []


def get_alpaca_paper_account(
    env: dict[str, str],
    *,
    transport: Transport | None = None,
) -> PaperBrokerAccountStatus:
    transport = transport or _default_transport
    pol, warns, blocks = evaluate_alpaca_paper_policy(env)
    now = datetime.now(timezone.utc)
    if pol != PaperBrokerPolicyStatus.PAPER_READY:
        return PaperBrokerAccountStatus(
            policy_status=pol,
            trading_blocked_reason=blocks[0] if blocks else None,
            warnings=warns + blocks,
            retrieved_at_utc=now,
        )
    key = env["ALPACA_API_KEY"].strip()
    secret = env["ALPACA_API_SECRET"].strip()
    base = (env.get("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
    url = f"{base}/v2/account"
    try:
        code, body = transport(
            url,
            {"Authorization": _auth_header(key, secret)},
            "GET",
        )
    except (OSError, HTTPError, URLError) as exc:
        return PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.DEGRADED,
            trading_blocked_reason="TRANSPORT_ERROR",
            warnings=warns + [f"{exc.__class__.__name__}"],
            retrieved_at_utc=now,
        )
    if code != 200:
        return PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.DEGRADED,
            trading_blocked_reason=f"HTTP_{code}",
            warnings=warns,
            retrieved_at_utc=now,
        )
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return PaperBrokerAccountStatus(
            policy_status=PaperBrokerPolicyStatus.DEGRADED,
            trading_blocked_reason="JSON_PARSE",
            retrieved_at_utc=now,
        )
    return PaperBrokerAccountStatus(
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        account_id=str(payload.get("id") or "") or None,
        equity=float(payload["equity"]) if payload.get("equity") is not None else None,
        buying_power=float(payload["buying_power"]) if payload.get("buying_power") is not None else None,
        currency=str(payload.get("currency") or "") or None,
        paper_endpoint_verified="paper-api" in base,
        warnings=warns,
        retrieved_at_utc=now,
    )


def list_alpaca_paper_positions(
    env: dict[str, str],
    *,
    transport: Transport | None = None,
) -> tuple[PaperBrokerPolicyStatus, list[PaperBrokerPositionSnapshot], list[str]]:
    transport = transport or _default_transport
    pol, warns, blocks = evaluate_alpaca_paper_policy(env)
    notes = warns + blocks
    if pol != PaperBrokerPolicyStatus.PAPER_READY:
        return pol, [], notes
    key = env["ALPACA_API_KEY"].strip()
    secret = env["ALPACA_API_SECRET"].strip()
    base = (env.get("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
    url = f"{base}/v2/positions"
    try:
        code, body = transport(url, {"Authorization": _auth_header(key, secret)}, "GET")
    except (OSError, HTTPError, URLError) as exc:
        return PaperBrokerPolicyStatus.DEGRADED, [], notes + [f"{exc.__class__.__name__}"]
    if code != 200:
        return PaperBrokerPolicyStatus.DEGRADED, [], notes + [f"HTTP_{code}"]
    try:
        rows = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return PaperBrokerPolicyStatus.DEGRADED, [], notes + ["JSON_PARSE"]
    if not isinstance(rows, list):
        return PaperBrokerPolicyStatus.DEGRADED, [], notes + ["UNEXPECTED_SHAPE"]
    out: list[PaperBrokerPositionSnapshot] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            out.append(
                PaperBrokerPositionSnapshot(
                    symbol=str(row.get("symbol") or ""),
                    qty=float(row.get("qty", 0) or 0),
                    market_value=float(row["market_value"]) if row.get("market_value") is not None else None,
                    avg_entry_price=float(row["avg_entry_price"])
                    if row.get("avg_entry_price") is not None
                    else None,
                )
            )
        except (TypeError, ValueError):
            continue
    return PaperBrokerPolicyStatus.PAPER_READY, out, notes


def dry_run_paper_order(intent: PaperBrokerOrderIntent, env: dict[str, str]) -> PaperBrokerOrderResult:
    pol, _, blocks = evaluate_alpaca_paper_policy(env)
    now = datetime.now(timezone.utc)
    if pol != PaperBrokerPolicyStatus.PAPER_READY:
        return PaperBrokerOrderResult(
            ok=False,
            policy_status=pol,
            dry_run=True,
            blockers=blocks,
            retrieved_at_utc=now,
        )
    return PaperBrokerOrderResult(
        ok=True,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY,
        dry_run=True,
        evidence_redacted={
            "symbol": intent.symbol,
            "side": intent.side,
            "qty": intent.qty,
            "order_type": intent.order_type,
        },
        warnings=["DRY_RUN_NO_SUBMISSION"],
        retrieved_at_utc=now,
    )


def submit_paper_order(
    intent: PaperBrokerOrderIntent,
    env: dict[str, str],
    *,
    transport: Transport | None = None,
) -> PaperBrokerOrderResult:
    transport = transport or _default_transport
    pol, warns, blocks = evaluate_alpaca_paper_policy(env)
    now = datetime.now(timezone.utc)
    if pol != PaperBrokerPolicyStatus.PAPER_READY:
        return PaperBrokerOrderResult(
            ok=False,
            policy_status=pol,
            dry_run=False,
            blockers=blocks,
            retrieved_at_utc=now,
        )
    key = env["ALPACA_API_KEY"].strip()
    secret = env["ALPACA_API_SECRET"].strip()
    base = (env.get("ALPACA_BASE_URL") or "https://paper-api.alpaca.markets").rstrip("/")
    url = f"{base}/v2/orders"
    body_obj: dict[str, Any] = {
        "symbol": intent.symbol.upper(),
        "qty": str(intent.qty),
        "side": intent.side,
        "type": intent.order_type,
        "time_in_force": intent.time_in_force,
    }
    if intent.order_type == "limit" and intent.limit_price is not None:
        body_obj["limit_price"] = str(intent.limit_price)
    raw = json.dumps(body_obj).encode("utf-8")
    try:
        req = Request(
            url,
            data=raw,
            headers={
                "Authorization": _auth_header(key, secret),
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urlopen(req, timeout=30) as resp:  # noqa: S310
            code = int(getattr(resp, "status", 200) or 200)
            rb = resp.read()
    except (OSError, HTTPError, URLError) as exc:
        return PaperBrokerOrderResult(
            ok=False,
            policy_status=PaperBrokerPolicyStatus.DEGRADED,
            dry_run=False,
            blockers=[exc.__class__.__name__],
            warnings=warns,
            retrieved_at_utc=now,
        )
    try:
        payload = json.loads(rb.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        payload = {"parse_error": True}
    ok = 200 <= code < 300
    redacted = {
        "id": payload.get("id") if isinstance(payload, dict) else None,
        "status": payload.get("status") if isinstance(payload, dict) else None,
        "symbol": intent.symbol,
        "side": intent.side,
    }
    return PaperBrokerOrderResult(
        ok=ok,
        policy_status=PaperBrokerPolicyStatus.PAPER_READY if ok else PaperBrokerPolicyStatus.DEGRADED,
        dry_run=False,
        broker_order_id=str(payload.get("id")) if isinstance(payload, dict) and payload.get("id") else None,
        status=str(payload.get("status")) if isinstance(payload, dict) else None,
        evidence_redacted=redacted,
        warnings=warns + ([] if ok else [f"HTTP_{code}"]),
        retrieved_at_utc=now,
    )


__all__ = [
    "dry_run_paper_order",
    "evaluate_alpaca_paper_policy",
    "get_alpaca_paper_account",
    "list_alpaca_paper_positions",
    "submit_paper_order",
]
