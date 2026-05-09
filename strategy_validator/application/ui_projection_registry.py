"""Read-plane projection registry cockpit payload.

This surface inventories the repo's registered projection families and any observed
``ORACLE_PROJECTION_ARTIFACT_INDEX.json`` files. It is intentionally read-only:
it never triggers rebuilds, checkpoint writes, ledger mutations, or projection
backfills from the UI/API surface.
"""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.application.projection_backfill import get_projection_registry

_SCHEMA_VERSION = "ui_projection_registry/v1"
_INDEX_NAME = "ORACLE_PROJECTION_ARTIFACT_INDEX.json"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _coerce_root(repo_root: str | Path | None = None, search_root: str | Path | None = None) -> Path:
    base = Path(repo_root).expanduser() if repo_root else Path.cwd()
    if search_root is None or not str(search_root).strip():
        return base.resolve()
    p = Path(search_root).expanduser()
    return p.resolve() if p.is_absolute() else (base / p).resolve()


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return raw if isinstance(raw, dict) else None


def _as_list(value: object) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    return []


def _contains(value: object, needle: str | None) -> bool:
    if not needle:
        return True
    return needle.strip().lower() in str(value or "").lower()


def _norm_set(values: tuple[str, ...] | list[str] | None) -> set[str]:
    return {str(v).strip().lower() for v in (values or ()) if str(v).strip()}


def _discover_indexes(root: Path) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    if not root.exists():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_missing"}]
    if not root.is_dir():
        return [], [{"path": str(root.as_posix()), "reason": "search_root_not_directory"}]
    observed: list[dict[str, Any]] = []
    invalid: list[dict[str, str]] = []
    for path in sorted(root.rglob(_INDEX_NAME)):
        raw = _read_json(path)
        if raw is None:
            invalid.append({"path": str(path.as_posix()), "reason": "invalid_json_or_not_object"})
            continue
        if raw.get("schema_version") != "oracle_projection_artifact_index/v1":
            invalid.append({"path": str(path.as_posix()), "reason": "unexpected_schema_version"})
            continue
        entries = raw.get("entries")
        if not isinstance(entries, list):
            invalid.append({"path": str(path.as_posix()), "reason": "entries_not_list"})
            continue
        for item in entries:
            if not isinstance(item, dict):
                invalid.append({"path": str(path.as_posix()), "reason": "entry_not_object"})
                continue
            observed.append({
                "index_path": str(path.as_posix()),
                "registry_path": item.get("registry_path"),
                "projection_family": item.get("projection_family"),
                "projection_label": item.get("projection_label"),
                "projection_version": item.get("projection_version"),
                "generated_at_utc": item.get("generated_at_utc"),
                "projection_digest_sha256": item.get("projection_digest_sha256"),
                "source_artifact_count": item.get("source_artifact_count", 0),
                "output_artifact_count": item.get("output_artifact_count", 0),
                "source_artifact_labels": _as_list(item.get("source_artifact_labels")),
                "output_artifact_labels": _as_list(item.get("output_artifact_labels")),
                "output_artifact_paths": _as_list(item.get("output_artifact_paths")),
            })
    observed.sort(key=lambda item: (str(item.get("generated_at_utc") or ""), str(item.get("registry_path") or "")), reverse=True)
    return observed, invalid


def _latest_digest(items: list[dict[str, Any]]) -> str | None:
    for item in items:
        digest = item.get("projection_digest_sha256")
        if digest:
            return str(digest)
    return None


def _latest_generated(items: list[dict[str, Any]]) -> str | None:
    for item in items:
        generated = item.get("generated_at_utc")
        if generated:
            return str(generated)
    return None


def _entry_summary(entry: dict[str, Any]) -> str:
    bits = [str(entry.get("projection_family") or "UNKNOWN"), f"label={entry.get('projection_label') or 'UNKNOWN'}"]
    bits.append(f"observed={entry.get('observed_artifact_count') or 0}")
    if entry.get("supports_checkpoints"):
        bits.append("checkpoints=true")
    if entry.get("latest_generated_at_utc"):
        bits.append(f"latest={entry.get('latest_generated_at_utc')}")
    return " · ".join(bits)


def _matches_entry(
    entry: dict[str, Any],
    *,
    families: set[str],
    labels: set[str],
    supports_checkpoints: bool | None,
    output_label_contains: str | None,
    handler_contains: str | None,
) -> bool:
    if families and str(entry.get("projection_family") or "").lower() not in families:
        return False
    if labels and str(entry.get("projection_label") or "").lower() not in labels:
        return False
    if supports_checkpoints is not None and bool(entry.get("supports_checkpoints")) is not supports_checkpoints:
        return False
    if output_label_contains and not any(_contains(label, output_label_contains) for label in _as_list(entry.get("output_artifact_labels"))):
        return False
    if not _contains(entry.get("rebuild_handler"), handler_contains):
        return False
    return True


def _counts(entries: list[dict[str, Any]], field: str) -> dict[str, int]:
    counter: Counter[str] = Counter()
    for entry in entries:
        counter[str(entry.get(field) or "UNKNOWN")] += 1
    return dict(sorted(counter.items()))


def build_ui_projection_registry_payload(
    *,
    repo_root: str | Path | None = None,
    search_root: str | Path | None = None,
    projection_family: tuple[str, ...] = (),
    projection_label: tuple[str, ...] = (),
    supports_checkpoints: bool | None = None,
    output_label_contains: str | None = None,
    handler_contains: str | None = None,
    limit: int = 200,
    include_artifact_entries: bool = False,
) -> dict[str, Any]:
    root = _coerce_root(repo_root=repo_root, search_root=search_root)
    registered = get_projection_registry()
    observed, invalid = _discover_indexes(root)
    observed_by_key: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for item in observed:
        observed_by_key[(str(item.get("projection_family") or ""), str(item.get("projection_label") or ""))].append(item)

    entries: list[dict[str, Any]] = []
    registered_keys: set[tuple[str, str]] = set()
    for record in registered:
        key = (record.projection_family, record.projection_label)
        registered_keys.add(key)
        artifacts = observed_by_key.get(key, [])
        artifact_output_labels = sorted({label for item in artifacts for label in _as_list(item.get("output_artifact_labels"))})
        output_labels = tuple(record.output_artifact_labels) or tuple(artifact_output_labels)
        entry: dict[str, Any] = {
            "projection_family": record.projection_family,
            "projection_label": record.projection_label,
            "registered": True,
            "supports_checkpoints": record.supports_checkpoints,
            "rebuild_handler": record.rebuild_handler,
            "output_artifact_labels": list(output_labels),
            "registered_output_artifact_labels": list(record.output_artifact_labels),
            "observed_artifact_count": len(artifacts),
            "latest_generated_at_utc": _latest_generated(artifacts),
            "latest_projection_digest_sha256": _latest_digest(artifacts),
            "registry_paths": [str(item.get("registry_path")) for item in artifacts if item.get("registry_path")],
            "output_artifact_paths": [path for item in artifacts for path in _as_list(item.get("output_artifact_paths"))],
        }
        entry["summary_line"] = _entry_summary(entry)
        if include_artifact_entries:
            entry["artifact_entries"] = artifacts
        entries.append(entry)

    orphan_artifact_entries = [item for item in observed if (str(item.get("projection_family") or ""), str(item.get("projection_label") or "")) not in registered_keys]
    families = _norm_set(projection_family)
    labels = _norm_set(projection_label)
    filtered = [
        entry
        for entry in entries
        if _matches_entry(
            entry,
            families=families,
            labels=labels,
            supports_checkpoints=supports_checkpoints,
            output_label_contains=output_label_contains,
            handler_contains=handler_contains,
        )
    ]
    capped_limit = max(1, min(int(limit or 200), 1000))
    returned = filtered[:capped_limit]
    degraded: list[str] = []
    if invalid:
        degraded.append("INVALID_PROJECTION_ARTIFACT_INDEX_PRESENT")
    if orphan_artifact_entries:
        degraded.append("UNREGISTERED_PROJECTION_ARTIFACTS_PRESENT")
    if any(int(entry.get("observed_artifact_count") or 0) == 0 for entry in entries):
        degraded.append("REGISTERED_PROJECTIONS_WITHOUT_OBSERVED_ARTIFACTS")
    return {
        "schema_version": _SCHEMA_VERSION,
        "generated_at_utc": _utc_now(),
        "read_plane_only": True,
        "mutation_authority": "none_read_plane",
        "backfill_authority": "none_read_plane",
        "search_root": str(root.as_posix()),
        "filters": {
            "projection_family": list(families),
            "projection_label": list(labels),
            "supports_checkpoints": supports_checkpoints,
            "output_label_contains": output_label_contains,
            "handler_contains": handler_contains,
            "limit": capped_limit,
            "include_artifact_entries": include_artifact_entries,
        },
        "summary": {
            "registered_projection_count": len(entries),
            "filtered_projection_count": len(filtered),
            "returned_projection_count": len(returned),
            "observed_artifact_entry_count": len(observed),
            "orphan_artifact_entry_count": len(orphan_artifact_entries),
            "invalid_index_artifact_count": len(invalid),
            "checkpoint_capable_count": sum(1 for entry in entries if entry.get("supports_checkpoints")),
            "registered_without_observed_artifacts_count": sum(1 for entry in entries if int(entry.get("observed_artifact_count") or 0) == 0),
        },
        "family_counts": _counts(filtered, "projection_family"),
        "label_counts": _counts(filtered, "projection_label"),
        "entries": returned,
        "orphan_artifact_entries": orphan_artifact_entries[:50],
        "invalid_index_artifacts": invalid[:50],
        "degraded": degraded,
        "guardrails": [
            "read_plane_only_no_projection_backfill_execution",
            "no_checkpoint_write_authority",
            "no_ledger_mutation_authority",
            "observed_artifacts_are_inventory_evidence_not_freshness_certification",
        ],
    }


__all__ = ["build_ui_projection_registry_payload"]
