from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _relative_or_absolute(path: Path, *, repo_root: Path | None) -> str:
    resolved = path.resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def build_projection_artifact_index_entry(*, registry_path: Path, registry: dict[str, Any], repo_root: Path | None = None) -> dict[str, Any]:
    return {
        "registry_path": _relative_or_absolute(registry_path, repo_root=repo_root),
        "projection_label": registry.get("projection_label"),
        "projection_family": registry.get("projection_family"),
        "projection_version": registry.get("projection_version"),
        "generated_at_utc": registry.get("generated_at_utc"),
        "projection_digest_sha256": registry.get("projection_digest_sha256"),
        "source_artifact_count": registry.get("source_artifact_count", 0),
        "output_artifact_count": registry.get("output_artifact_count", 0),
        "source_artifact_labels": [item.get("artifact_label") for item in registry.get("source_artifacts", [])],
        "output_artifact_labels": [item.get("artifact_label") for item in registry.get("output_artifacts", [])],
        "output_artifact_paths": [item.get("path") for item in registry.get("output_artifacts", [])],
    }


def build_projection_artifact_index(
    *,
    existing_entries: list[dict[str, Any]],
    registry_path: Path,
    registry: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    new_entry = build_projection_artifact_index_entry(registry_path=registry_path, registry=registry, repo_root=repo_root)
    remaining = [entry for entry in existing_entries if entry.get("registry_path") != new_entry["registry_path"]]
    entries = remaining + [new_entry]
    entries.sort(key=lambda item: ((item.get("generated_at_utc") or ""), (item.get("registry_path") or "")))
    return {
        "schema_version": "oracle_projection_artifact_index/v1",
        "generated_at_utc": (generated_at_utc or _utc_now()).isoformat(),
        "entry_count": len(entries),
        "entries": entries,
    }


def load_projection_artifact_index(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_projection_artifact_index(path: Path, index: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(index, indent=2, default=str) + "\n", encoding="utf-8")


def upsert_projection_artifact_index(
    *,
    index_path: Path,
    registry_path: Path,
    registry: dict[str, Any],
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    existing_entries: list[dict[str, Any]] = []
    if index_path.exists():
        existing = load_projection_artifact_index(index_path)
        existing_entries = list(existing.get("entries", []))
    index = build_projection_artifact_index(
        existing_entries=existing_entries,
        registry_path=registry_path,
        registry=registry,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
    write_projection_artifact_index(index_path, index)
    return index
