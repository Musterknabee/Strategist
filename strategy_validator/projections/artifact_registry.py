from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from strategy_validator.projections.artifact_index import upsert_projection_artifact_index


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _sha256_json(payload: dict[str, Any]) -> str:
    stable = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return hashlib.sha256(stable).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _coerce_schema_version(payload: Any) -> str | None:
    if hasattr(payload, "schema_version"):
        return getattr(payload, "schema_version")
    if isinstance(payload, dict):
        value = payload.get("schema_version")
        return str(value) if value else None
    return None


def _relative_or_absolute(path: Path, *, repo_root: Path | None) -> str:
    resolved = path.resolve()
    if repo_root is None:
        return str(resolved)
    try:
        return str(resolved.relative_to(repo_root.resolve()))
    except ValueError:
        return str(resolved)


def build_projection_source_descriptor(
    *,
    artifact_label: str,
    path: Path,
    payload: Any | None = None,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    descriptor: dict[str, Any] = {
        "artifact_label": artifact_label,
        "path": _relative_or_absolute(path, repo_root=repo_root),
        "exists": path.exists(),
    }
    if path.exists():
        descriptor["sha256"] = _sha256_file(path)
        descriptor["size_bytes"] = path.stat().st_size
        descriptor["modified_at_utc"] = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc).isoformat()
    schema_version = _coerce_schema_version(payload)
    if schema_version:
        descriptor["schema_version"] = schema_version
    return descriptor


def build_projection_artifact_registry(
    *,
    projection_label: str,
    projection_family: str,
    projection_version: str,
    source_descriptors: Iterable[dict[str, Any]],
    output_paths: Iterable[Path] = (),
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    sources = list(source_descriptors)
    outputs = [
        build_projection_source_descriptor(
            artifact_label=f"output:{path.name}",
            path=path,
            payload={"schema_version": projection_version} if path.suffix == ".json" else None,
            repo_root=repo_root,
        )
        for path in output_paths
    ]
    registry = {
        "schema_version": "oracle_projection_artifact_registry/v1",
        "generated_at_utc": (generated_at_utc or _utc_now()).isoformat(),
        "projection_label": projection_label,
        "projection_family": projection_family,
        "projection_version": projection_version,
        "source_artifact_count": len(sources),
        "output_artifact_count": len(outputs),
        "source_artifacts": sources,
        "output_artifacts": outputs,
    }
    registry["projection_digest_sha256"] = _sha256_json(
        {key: value for key, value in registry.items() if key != "generated_at_utc"}
    )
    return registry


def write_projection_artifact_registry(path: Path, registry: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, indent=2, default=str) + "\n", encoding="utf-8")


def write_projection_artifact_registry_with_index(
    path: Path,
    registry: dict[str, Any],
    *,
    repo_root: Path | None = None,
    index_path: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    write_projection_artifact_registry(path, registry)
    resolved_index_path = index_path or path.with_name("ORACLE_PROJECTION_ARTIFACT_INDEX.json")
    return upsert_projection_artifact_index(
        index_path=resolved_index_path,
        registry_path=path,
        registry=registry,
        repo_root=repo_root,
        generated_at_utc=generated_at_utc,
    )
