"""Shared helpers for semantic validator handoff audit-packet read planes."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from typing import Any, Iterable

_SCHEMA_VERSION = "ui_semantic_validator_handoff_audit_packet/v1"
_LIMIT_MAX = 1000

_DETAIL_ROUTES = {
    "handoff": "/ui/semantic-validator-handoff",
    "lineage": "/ui/semantic-validator-handoff/lineage",
    "remediation": "/ui/semantic-validator-handoff/remediation",
    "review": "/ui/semantic-validator-handoff/review",
    "decision": "/ui/semantic-validator-handoff/decision",
    "signoff": "/ui/semantic-validator-handoff/signoff",
    "custody": "/ui/semantic-validator-handoff/custody",
    "archive": "/ui/semantic-validator-handoff/archive",
    "closure": "/ui/semantic-validator-handoff/closure",
    "continuity": "/ui/semantic-validator-handoff/continuity",
    "runbook": "/ui/semantic-validator-handoff/runbook",
    "exceptions": "/ui/semantic-validator-handoff/exceptions",
    "timeline": "/ui/semantic-validator-handoff/timeline",
    "evidence_gaps": "/ui/semantic-validator-handoff/evidence-gaps",
    "audit_packet": "/ui/semantic-validator-handoff/audit-packet",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(value: object) -> str:
    return str(value or "").strip()


def _norm(value: object) -> str:
    return _s(value).upper()


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {_norm(value) for value in values or () if _s(value)}


def _contains(value: object, needle: str | None) -> bool:
    return True if not needle else needle.strip().lower() in str(value or "").lower()


def _counts(rows: Iterable[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for row in rows:
        counter[_s(row.get(field)) or "UNKNOWN"] += 1
    return dict(sorted(counter.items()))


def _digest(payload: object) -> str:
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _authority() -> dict[str, Any]:
    return {
        "read_plane_only": True,
        "packet_materialization_allowed": False,
        "external_artifact_write_allowed": False,
        "artifact_mutation_allowed": False,
        "validator_submission_allowed": False,
        "adjudication_allowed": False,
        "promotion_allowed": False,
        "execution_allowed": False,
        "authority_boundary": "read_plane_only_consolidated_audit_visibility_no_writes_no_submit_no_execute",
    }
