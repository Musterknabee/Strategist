"""Deterministic normalization of provider sample files into PIT-aware observations (no network)."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from strategy_validator.contracts.provider_capabilities import capability_by_provider_id
from strategy_validator.contracts.provider_observation import (
    FreshnessClassification,
    ProviderObservationRecord,
    RevisionPolicy,
)


def _sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _canonical_json_digest(obj: dict[str, Any]) -> str:
    return _sha256_hex(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def _extract_sec(payload: dict[str, Any], retrieved_at: str) -> tuple[str | None, str | None, FreshnessClassification, RevisionPolicy]:
    filings = payload.get("filings", {})
    recent = filings.get("recent") if isinstance(filings, dict) else None
    if isinstance(recent, dict):
        fd = recent.get("filingDate")
        if isinstance(fd, list) and fd:
            return str(fd[0]), str(fd[0]), FreshnessClassification.RELEASE_OR_OBSERVATION, RevisionPolicy.REVISION_SENSITIVE
        if isinstance(fd, str):
            return fd, fd, FreshnessClassification.RELEASE_OR_OBSERVATION, RevisionPolicy.REVISION_SENSITIVE
    return None, None, FreshnessClassification.BEST_EFFORT_AS_OF, RevisionPolicy.SNAPSHOT_ONLY


def _extract_fred(payload: dict[str, Any], retrieved_at: str) -> tuple[str | None, FreshnessClassification, RevisionPolicy]:
    obs = payload.get("observations")
    if isinstance(obs, list) and obs:
        last = obs[-1]
        if isinstance(last, dict) and last.get("date"):
            d = str(last["date"])
            return d, FreshnessClassification.RELEASE_OR_OBSERVATION, RevisionPolicy.OFFICIAL_VINTAGE
    return None, FreshnessClassification.BEST_EFFORT_AS_OF, RevisionPolicy.REVISION_SENSITIVE


def _extract_world_bank(payload: list | dict, retrieved_at: str) -> tuple[str | None, FreshnessClassification]:
    try:
        if isinstance(payload, list) and len(payload) > 1:
            inner = payload[1]
            if isinstance(inner, list) and inner:
                row = inner[0]
                if isinstance(row, dict) and row.get("date"):
                    return str(row["date"]), FreshnessClassification.RELEASE_OR_OBSERVATION
    except (IndexError, KeyError, TypeError):
        pass
    return None, FreshnessClassification.BEST_EFFORT_AS_OF


def normalize_one_sample(
    *,
    provider_id: str,
    manifest_row: dict[str, Any],
    raw_bytes: bytes,
    samples_dir: Path,
) -> ProviderObservationRecord | None:
    caps = capability_by_provider_id()
    cap = caps.get(provider_id)
    if cap is None:
        return None
    retrieved = str(manifest_row.get("retrieved_at_utc") or datetime.now(timezone.utc).isoformat())
    endpoint = str(manifest_row.get("endpoint", ""))
    raw_d = _sha256_hex(raw_bytes)

    observed: str | None = None
    as_of: str | None = None
    published: str | None = None
    release_ts: str | None = None
    sym: str | None = manifest_row.get("query_params", {}).get("symbol") if isinstance(manifest_row.get("query_params"), dict) else None
    series_id: str | None = None
    geo: str | None = None
    fresh: FreshnessClassification = FreshnessClassification.UNKNOWN
    revpol: RevisionPolicy = RevisionPolicy.UNKNOWN
    notes: list[str] = []

    classified = str(manifest_row.get("classified_status", ""))
    if classified != "OK" or manifest_row.get("http_status") != 200:
        notes.append(f"sample_not_ok:{classified}")
        rec = ProviderObservationRecord(
            provider_id=provider_id,
            source_endpoint_redacted=endpoint[:200],
            retrieved_at_utc=retrieved,
            raw_sample_digest=raw_d,
            normalized_digest=_canonical_json_digest({"provider_id": provider_id, "skipped": True}),
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            freshness_classification=FreshnessClassification.UNKNOWN,
            revision_policy=RevisionPolicy.UNKNOWN,
            may_be_used_for_validation=False,
            may_gate_live_promotion=False,
            evidence_uri=(samples_dir / str(manifest_row.get("sample_path", "missing"))).as_posix(),
            notes=tuple(notes),
        )
        return rec

    payload: Any = None
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeError):
        notes.append("non_json_body")
        payload = None

    if isinstance(payload, dict):
        if provider_id == "sec_edgar":
            observed, as_of, fresh, revpol = _extract_sec(payload, retrieved)
            release_ts = as_of
        elif provider_id == "fred":
            series_id = str(manifest_row.get("query_params", {}).get("series_id", "")) or None
            od, fresh, revpol = _extract_fred(payload, retrieved)
            observed = od
            as_of = od or retrieved
        elif provider_id == "world_bank_open_data":
            geo = manifest_row.get("query_params", {}).get("country") if isinstance(manifest_row.get("query_params"), dict) else None
            od, fresh = _extract_world_bank(payload, retrieved)
            observed = od
            as_of = od or retrieved
            revpol = RevisionPolicy.OFFICIAL_VINTAGE
        else:
            if isinstance(payload.get("data"), list) and payload["data"]:
                fresh = FreshnessClassification.BEST_EFFORT_AS_OF
                as_of = retrieved
            else:
                as_of = retrieved
                fresh = FreshnessClassification.BEST_EFFORT_AS_OF
            revpol = RevisionPolicy.SNAPSHOT_ONLY
    else:
        as_of = retrieved
        fresh = FreshnessClassification.BEST_EFFORT_AS_OF
        revpol = RevisionPolicy.SNAPSHOT_ONLY
        notes.append("unstructured_json")

    if as_of is None:
        as_of = retrieved
    if fresh == FreshnessClassification.UNKNOWN:
        fresh = FreshnessClassification.BEST_EFFORT_AS_OF
    if revpol == RevisionPolicy.UNKNOWN:
        revpol = RevisionPolicy.SNAPSHOT_ONLY

    official = cap.default_trust_level.value == "OFFICIAL_SOURCE"
    may_validate = official and fresh != FreshnessClassification.UNKNOWN and as_of is not None
    may_gate = bool(cap.may_gate_live_promotion) and may_validate

    norm_core = {
        "as_of_utc": as_of,
        "observed_at_utc": observed,
        "provider_id": provider_id,
        "trust": cap.default_trust_level.value,
    }
    norm_digest = _canonical_json_digest(norm_core)

    return ProviderObservationRecord(
        provider_id=provider_id,
        source_endpoint_redacted=endpoint[:240],
        retrieved_at_utc=retrieved,
        observed_at_utc=observed,
        as_of_utc=as_of,
        published_at_utc=published,
        release_timestamp=release_ts,
        symbol=str(sym) if sym else None,
        series_id=series_id,
        geography=str(geo) if geo else None,
        raw_sample_digest=raw_d,
        normalized_digest=norm_digest,
        trust_level=cap.default_trust_level.value,
        pit_suitability=cap.pit_suitability.value,
        license_scope="research_optional",
        freshness_classification=fresh,
        is_revision_sensitive=revpol == RevisionPolicy.REVISION_SENSITIVE,
        revision_policy=revpol,
        may_be_used_for_validation=may_validate,
        may_gate_live_promotion=may_gate,
        evidence_uri=(samples_dir / str(manifest_row.get("sample_path", "unknown"))).as_posix(),
        notes=tuple(notes),
    )


def normalize_sample_bundle(
    *,
    manifest_path: Path,
    samples_dir: Path,
) -> tuple[ProviderObservationRecord, ...]:
    if not manifest_path.is_file():
        return ()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()
    out: list[ProviderObservationRecord] = []
    for row in manifest.get("entries", []):
        pid = row.get("provider_id")
        if not isinstance(pid, str):
            continue
        sp = row.get("sample_path")
        if not isinstance(sp, str):
            continue
        path = samples_dir / sp
        if not path.is_file():
            continue
        raw = path.read_bytes()
        rec = normalize_one_sample(provider_id=pid, manifest_row=row, raw_bytes=raw, samples_dir=samples_dir)
        if rec:
            out.append(rec)
    return tuple(sorted(out, key=lambda r: r.provider_id))


__all__ = ["normalize_one_sample", "normalize_sample_bundle"]
