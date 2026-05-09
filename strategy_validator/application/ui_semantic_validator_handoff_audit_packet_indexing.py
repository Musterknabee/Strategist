"""Indexing helpers for semantic validator handoff audit-packet inputs."""
from __future__ import annotations

from typing import Any, Iterable

from strategy_validator.application.ui_semantic_validator_handoff_audit_packet_common import _s


def _row_key(row: dict[str, Any]) -> str:
    for key in ("continuity_id", "chain_id", "experiment_id"):
        value = _s(row.get(key))
        if value:
            return value
    return "UNKNOWN"


def _index_rows(rows: Iterable[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    indexed: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        keys = {_s(row.get("continuity_id")), _s(row.get("chain_id")), _s(row.get("experiment_id"))}
        for key in {item for item in keys if item} or {"UNKNOWN"}:
            indexed.setdefault(key, []).append(row)
    return indexed


def _related(indexed: dict[str, list[dict[str, Any]]], continuity: dict[str, Any]) -> list[dict[str, Any]]:
    seen: set[int] = set()
    related: list[dict[str, Any]] = []
    for key in (_s(continuity.get("continuity_id")), _s(continuity.get("chain_id")), _s(continuity.get("experiment_id"))):
        if not key:
            continue
        for row in indexed.get(key, []):
            ident = id(row)
            if ident in seen:
                continue
            seen.add(ident)
            related.append(row)
    return related
