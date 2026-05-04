"""IO helpers for provider historical snapshot runs (no secrets in logs)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.provider_historical_data import (
    ProviderDataIngestionManifest,
    ProviderIngestionRuntimeStatus,
)
from strategy_validator.contracts.provider_historical_snapshot import (
    ProviderHistoricalSnapshotManifest,
    ProviderHistoricalSnapshotRequest,
    ProviderHistoricalSnapshotRun,
    ProviderHistoricalSnapshotStatus,
)
from strategy_validator.research.strategy_batch_digests import canonical_json_sha256


def map_ingestion_runtime_to_snapshot_status(
    st: ProviderIngestionRuntimeStatus | str,
) -> ProviderHistoricalSnapshotStatus:
    if isinstance(st, str):
        st = ProviderIngestionRuntimeStatus(st)
    mapping = {
        ProviderIngestionRuntimeStatus.OK: ProviderHistoricalSnapshotStatus.OK,
        ProviderIngestionRuntimeStatus.PENDING_KEY: ProviderHistoricalSnapshotStatus.PENDING_KEY,
        ProviderIngestionRuntimeStatus.UNAVAILABLE: ProviderHistoricalSnapshotStatus.PROVIDER_UNAVAILABLE,
        ProviderIngestionRuntimeStatus.BLOCKED: ProviderHistoricalSnapshotStatus.BLOCKED_BY_POLICY,
        ProviderIngestionRuntimeStatus.DEGRADED: ProviderHistoricalSnapshotStatus.RATE_LIMITED,
    }
    return mapping.get(st, ProviderHistoricalSnapshotStatus.FAILED_VALIDATION)


def manifest_from_legacy_ingestion(
    m: ProviderDataIngestionManifest,
    *,
    key_configured: bool | None = None,
    access_type: str = "api",
    trust_level: str = "unverified_freemium",
) -> ProviderHistoricalSnapshotManifest:
    if key_configured is not None:
        kc = bool(key_configured)
    else:
        kc = m.provider_status == ProviderIngestionRuntimeStatus.OK
    st = map_ingestion_runtime_to_snapshot_status(m.provider_status)
    return ProviderHistoricalSnapshotManifest(
        provider_id=m.provider_id,
        symbols=[m.symbol.strip().upper()],
        timeframe=m.timeframe,
        start_utc=m.start_utc,
        end_utc=m.end_utc,
        as_of_utc=m.as_of_utc,
        access_type=access_type,
        key_required=True,
        key_configured=kc,
        provider_status=st,
        pit_status=m.pit_status,
        license_scope=m.license_scope,
        trust_level=trust_level,
        retrieved_at_utc=m.retrieved_at_utc,
        bars_path=m.bars_path,
        bars_sha256=m.bars_sha256,
        row_count=m.row_count,
        warnings=list(m.warnings),
        blockers=list(m.blockers),
        manifest_sha256="",
        extra={},
    )


def finalize_manifest_sha(m: ProviderHistoricalSnapshotManifest) -> ProviderHistoricalSnapshotManifest:
    body = m.model_dump(mode="json")
    body.pop("manifest_sha256", None)
    digest = canonical_json_sha256(body)
    return m.model_copy(update={"manifest_sha256": digest})


def finalize_run_sha(r: ProviderHistoricalSnapshotRun) -> ProviderHistoricalSnapshotRun:
    body = r.model_dump(mode="json")
    body.pop("manifest_sha256", None)
    digest = canonical_json_sha256(body)
    return r.model_copy(update={"manifest_sha256": digest})


def parse_snapshot_manifest_dict(raw: dict[str, Any]) -> ProviderHistoricalSnapshotManifest:
    if raw.get("schema_version") == "provider_data_ingestion_manifest/v1":
        legacy = ProviderDataIngestionManifest.model_validate(raw)
        return finalize_manifest_sha(manifest_from_legacy_ingestion(legacy))
    return ProviderHistoricalSnapshotManifest.model_validate(raw)


def load_snapshot_manifest(path: Path) -> ProviderHistoricalSnapshotManifest:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("manifest must be a JSON object")
    m = parse_snapshot_manifest_dict(raw)
    if not m.manifest_sha256:
        m = finalize_manifest_sha(m)
    return m


def write_snapshot_run(
    run: ProviderHistoricalSnapshotRun,
    *,
    output_root: Path,
) -> Path:
    """Write ``{output_root}/latest/provider_historical_snapshot_run.json``."""
    latest_dir = output_root.resolve() / "latest"
    latest_dir.mkdir(parents=True, exist_ok=True)
    run = finalize_run_sha(run)
    path = latest_dir / "provider_historical_snapshot_run.json"
    path.write_text(json.dumps(run.model_dump(mode="json"), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return path


def ensure_latest_snapshot_dir(output_root: Path) -> Path:
    root = output_root.resolve() / "latest"
    root.mkdir(parents=True, exist_ok=True)
    return root


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


__all__ = [
    "ensure_latest_snapshot_dir",
    "finalize_manifest_sha",
    "finalize_run_sha",
    "load_snapshot_manifest",
    "manifest_from_legacy_ingestion",
    "map_ingestion_runtime_to_snapshot_status",
    "parse_snapshot_manifest_dict",
    "sha256_file",
    "write_snapshot_run",
]
