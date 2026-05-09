"""Shared helpers for the daily operator run composite read model."""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from strategy_validator.contracts.daily_operator_run import DailyOperatorRunComponent


def _as_dict(v: Any) -> dict[str, Any]:
    return v if isinstance(v, dict) else {}


def _as_list(v: Any) -> list[Any]:
    return v if isinstance(v, list) else []


def _strings(v: Any) -> list[str]:
    if isinstance(v, list):
        return [str(x) for x in v if x not in (None, "")]
    if v in (None, ""):
        return []
    return [str(v)]


def _int(v: Any) -> int:
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


def _safe(route: str, fn: Callable[[], dict[str, Any]]) -> tuple[dict[str, Any], list[str], list[str]]:
    try:
        p = fn()
    except Exception as exc:  # pragma: no cover
        return {}, [], [f"{route}:UNREADABLE:{type(exc).__name__}"]
    if not isinstance(p, dict):
        return {}, [], [f"{route}:INVALID_PAYLOAD"]
    return p, _strings(p.get("degraded")), []


def _component(component_id: str, title: str, source_route: str, status: str, posture: str, summary: dict[str, Any], warnings=None, blockers=None, actions=None, refs=None) -> DailyOperatorRunComponent:
    return DailyOperatorRunComponent(
        component_id=component_id,
        title=title,
        source_route=source_route,
        status=status,  # type: ignore[arg-type]
        posture=posture,
        summary=summary,
        warnings=sorted(set(warnings or [])),
        blockers=sorted(set(blockers or [])),
        recommended_actions=list(dict.fromkeys(actions or [])),
        evidence_refs=refs or [],
    )
