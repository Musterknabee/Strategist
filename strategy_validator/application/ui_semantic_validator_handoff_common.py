"""Shared helpers for semantic validator handoff read-plane."""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCHEMA_VERSION = "ui_semantic_validator_handoff/v1"
_KNOWN_SCHEMAS = {
    "semantic_adjudication_release_decision_ledger/v1": "decision_ledger",
    "semantic_adjudication_release_handoff_certificate/v1": "handoff_certificate",
    "semantic_validator_handoff_packet/v1": "validator_packet",
    "semantic_validator_handoff_packet_ingress_certificate/v1": "ingress_certificate",
}
_DEFAULT_RELATIVE_ROOTS = (
    Path("artifacts") / "research_integrity",
    Path("artifacts") / "semantic_release",
    Path("artifacts") / "semantic_validator_handoff",
    Path("artifacts") / "validator_handoff",
    Path("artifacts"),
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_root(repo_root: str | Path | None = None, search_root: str | Path | None = None) -> Path:
    base = Path(repo_root).expanduser() if repo_root else Path.cwd()
    if search_root is not None and str(search_root).strip():
        p = Path(search_root).expanduser()
        return p.resolve() if p.is_absolute() else (base / p).resolve()
    for relative in _DEFAULT_RELATIVE_ROOTS:
        candidate = (base / relative).resolve()
        if candidate.is_dir():
            return candidate
    return (base / _DEFAULT_RELATIVE_ROOTS[0]).resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _sha256(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {str(v).strip().upper() for v in (values or ()) if str(v).strip()}


def _contains(value: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _issue_haystack(entry: dict[str, Any]) -> str:
    parts = [str(entry.get("recommended_action") or ""), str(entry.get("summary_line") or "")]
    parts.extend(_as_list(entry.get("blocker_codes")))
    parts.extend(_as_list(entry.get("warning_codes")))
    parts.extend(_as_list(entry.get("issue_codes")))
    return "\n".join(parts)


def _counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter[str(entry.get(field) if entry.get(field) is not None else "UNKNOWN")] += 1
    return dict(sorted(counter.items()))


def _bool_counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter["true" if bool(entry.get(field)) else "false"] += 1
    return dict(sorted(counter.items()))


def _authority() -> dict[str, object]:
    return {
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "validator_submission_authority": "none_read_plane",
        "adjudication_authority": "none_read_plane",
        "promotion_authority": "none_read_plane",
        "execution_authority": "none_read_plane",
    }
