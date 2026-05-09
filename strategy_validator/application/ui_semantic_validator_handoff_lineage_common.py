"""Shared helpers for semantic validator handoff lineage read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_lineage/v1"
_CHAIN_KIND_ORDER = ("decision_ledger", "handoff_certificate", "validator_packet", "ingress_certificate")
_READY_ACTION = "REVIEW_READY_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE"
_REPAIR_ACTION = "REPAIR_SEMANTIC_VALIDATOR_HANDOFF_LINEAGE_BEFORE_VALIDATOR_REVIEW"
_LIMIT_MAX = 1000


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: object) -> str:
    return str(value or "").strip()


def _contains(value: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {_s(value).upper() for value in values or () if _s(value)}


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_s(row.get(field)) or "UNKNOWN"] += 1
    return dict(sorted(counter.items()))


def _entry_ref(entry: dict[str, Any] | None) -> dict[str, Any] | None:
    if entry is None:
        return None
    return {
        "artifact_kind": entry.get("artifact_kind"),
        "schema_version": entry.get("schema_version"),
        "artifact_id": entry.get("artifact_id"),
        "experiment_id": entry.get("experiment_id"),
        "ledger_id": entry.get("ledger_id"),
        "certificate_id": entry.get("certificate_id"),
        "packet_id": entry.get("packet_id"),
        "evidence_id": entry.get("evidence_id"),
        "payload_checksum": entry.get("payload_checksum"),
        "artifact_sha256": entry.get("artifact_sha256"),
        "artifact_path": entry.get("artifact_path"),
        "verified": bool(entry.get("verified")),
        "handoff_allowed": bool(entry.get("handoff_allowed")),
        "ready_for_validator_ingress": entry.get("ready_for_validator_ingress"),
        "recommended_action": entry.get("recommended_action"),
        "blocker_codes": _as_list(entry.get("blocker_codes")),
        "warning_codes": _as_list(entry.get("warning_codes")),
        "issue_codes": _as_list(entry.get("issue_codes")),
        "summary_line": entry.get("summary_line"),
    }


def _component_id(entry: dict[str, Any] | None) -> str:
    if entry is None:
        return "missing"
    return (
        _s(entry.get("artifact_id"))
        or _s(entry.get("packet_id"))
        or _s(entry.get("certificate_id"))
        or _s(entry.get("ledger_id"))
        or "unknown"
    )


def _find_first(entries: list[dict[str, Any]], field: str, value: object) -> dict[str, Any] | None:
    wanted = _s(value)
    if not wanted:
        return None
    for entry in entries:
        if _s(entry.get(field)) == wanted:
            return entry
    return None


def _find_first_by_any(entries: list[dict[str, Any]], pairs: Iterable[tuple[str, object]]) -> dict[str, Any] | None:
    for field, value in pairs:
        found = _find_first(entries, field, value)
        if found is not None:
            return found
    return None


def _link_digest(parts: Iterable[object]) -> str:
    payload = json.dumps([str(part or "") for part in parts], sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _authority() -> dict[str, Any]:
    return {
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
    }
