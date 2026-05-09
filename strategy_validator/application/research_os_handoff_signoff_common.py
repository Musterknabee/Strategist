"""Shared helpers for Research OS handoff signoff operations."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from strategy_validator.application.research_os_paths import artifact_root_directory

_SCHEMA = "ui_research_os_handoff_signoff/v1"

_SECRET_MARKERS = (
    "STRATEGY_VALIDATOR_API_TOKEN",
    "ALPACA_API_SECRET",
    "ALPACA_SECRET_KEY",
    "POLYGON_API_KEY",
    "TIINGO_API_KEY",
    "TWELVE_DATA_API_KEY",
    "PRIVATE_KEY",
    "BEARER ",
)


def _artifact_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    if artifact_root is not None:
        return artifact_root.expanduser().resolve()
    return artifact_root_directory(repo_root)

def research_os_handoff_signoff_root(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (_artifact_root(repo_root, artifact_root) / "research_os_handoff_signoff").resolve()

def research_os_handoff_verification_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_handoff_signoff_root(repo_root, artifact_root) / "latest" / "research_os_handoff_verification_result.json").resolve()

def research_os_handoff_reviewer_signoff_latest_path(repo_root: Path | None = None, artifact_root: Path | None = None) -> Path:
    return (research_os_handoff_signoff_root(repo_root, artifact_root) / "latest" / "research_os_handoff_reviewer_signoff.json").resolve()

def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None

def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str) + "\n", encoding="utf-8")

def _canonical_sha256(payload: Any) -> str:
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, default=str).encode("utf-8")).hexdigest()

def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def _contains_secret_marker(path: Path) -> bool:
    try:
        if not path.is_file() or path.stat().st_size > 5_000_000:
            return False
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return False
    upper = text.upper()
    return any(marker.upper() in upper for marker in _SECRET_MARKERS)

def _list(raw: dict[str, Any] | None, key: str, limit: int = 80) -> list[str]:
    value = raw.get(key) if isinstance(raw, dict) else []
    if not isinstance(value, list):
        return []
    rows = [str(x) for x in value if x is not None]
    if len(rows) > limit:
        return rows[:limit] + [f"{key.upper()}_TRUNCATED:{len(rows)}"]
    return rows

def _observed_handoff_spine(raw: dict[str, Any]) -> str:
    spine = {
        "handoff_id": raw.get("handoff_id"),
        "status": raw.get("status"),
        "decision": raw.get("decision"),
        "source_release_readiness_decision": raw.get("source_release_readiness_decision"),
        "source_policy_gate_decision": raw.get("source_policy_gate_decision"),
        "source_exception_status": raw.get("source_exception_status"),
        "checklist": [
            {
                "item_id": c.get("item_id"),
                "status": c.get("status"),
                "blockers": c.get("blockers", []),
                "warnings": c.get("warnings", []),
            }
            for c in raw.get("checklist", [])
            if isinstance(c, dict)
        ],
        "source_refs": [
            {
                "label": r.get("label"),
                "present": r.get("present"),
                "manifest_sha256": r.get("manifest_sha256"),
                "status_hint": r.get("status_hint"),
                "decision_hint": r.get("decision_hint"),
            }
            for r in raw.get("source_refs", [])
            if isinstance(r, dict)
        ],
    }
    return _canonical_sha256(spine)

def _observed_manifest_sha(raw: dict[str, Any]) -> str:
    payload = dict(raw)
    payload.pop("manifest_sha256", None)
    return _canonical_sha256(payload)

__all__ = [
    "_SCHEMA",
    "_artifact_root",
    "_canonical_sha256",
    "_contains_secret_marker",
    "_list",
    "_observed_handoff_spine",
    "_observed_manifest_sha",
    "_read_json",
    "_sha256_file",
    "_write_json",
    "research_os_handoff_reviewer_signoff_latest_path",
    "research_os_handoff_signoff_root",
    "research_os_handoff_verification_latest_path",
]
