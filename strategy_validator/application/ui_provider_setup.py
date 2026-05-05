"""Provider setup and freshness read model for the operator console."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from strategy_validator.contracts.provider_capabilities import capability_by_provider_id
from strategy_validator.contracts.provider_setup import ProviderSetupConsolePayload, ProviderSetupEntry
from strategy_validator.providers.health import build_provider_health_snapshot

_DEFAULT_FRESHNESS_MAX_AGE_SECONDS = 24 * 60 * 60


def _parse_positive_int(raw: str | None, default: int) -> int:
    if raw is None:
        return default
    try:
        parsed = int(raw.strip())
    except (TypeError, ValueError):
        return default
    if parsed <= 0:
        return default
    return parsed


def _parse_timestamp(raw: str | None) -> datetime | None:
    if not raw:
        return None
    text = raw.strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _freshness_age_seconds(raw: str | None, now: datetime) -> int | None:
    parsed = _parse_timestamp(raw)
    if parsed is None:
        return None
    age = int((now.astimezone(timezone.utc) - parsed).total_seconds())
    return max(age, 0)


def _freshness_class(*, classified_status: str, age_seconds: int | None, max_age_seconds: int) -> str:
    status = classified_status.upper()
    if status in {
        "AUTH_FAILED",
        "PLAN_LIMITED",
        "RATE_LIMITED",
        "ERROR",
        "HTTP_ERROR",
        "ENDPOINT_CHANGED",
        "PARSE_ERROR",
        "NETWORK_BLOCKED",
        "TEMPORARILY_UNAVAILABLE",
    }:
        return "DEGRADED"
    if status in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}:
        return "PENDING_SETUP"
    if status in {"NOT_CHECKED", "SKIPPED_NO_NETWORK"}:
        return "NOT_CHECKED"
    if age_seconds is None:
        return "UNKNOWN"
    if age_seconds > max_age_seconds:
        return "STALE"
    return "FRESH"


def _canonical_status(
    *,
    requires_secret: bool,
    configured: bool,
    classified_status: str,
    blockers: tuple[str, ...],
    freshness_class: str,
) -> str:
    status = classified_status.upper()
    if blockers:
        return "BLOCKED"
    if requires_secret and not configured:
        return "OPTIONAL_NOT_CONFIGURED"
    if status in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}:
        return "PENDING_KEY"
    if status in {"TEMPORARILY_UNAVAILABLE", "NETWORK_BLOCKED"}:
        return "UNAVAILABLE"
    if freshness_class == "STALE":
        return "STALE"
    if status in {"AUTH_FAILED", "PLAN_LIMITED", "RATE_LIMITED", "ENDPOINT_CHANGED", "PARSE_ERROR", "ERROR", "HTTP_ERROR"}:
        return "DEGRADED"
    if status in {"NOT_CHECKED", "SKIPPED_NO_NETWORK"}:
        return "UNKNOWN"
    if status == "OK":
        return "OK"
    return "UNKNOWN"


def _setup_status(*, requires_secret: bool, configured: bool, classified_status: str, blockers: tuple[str, ...]) -> str:
    status = classified_status.upper()
    if blockers:
        return "POLICY_BLOCKED"
    if requires_secret and not configured:
        return "MISSING_OPTIONAL_SECRET"
    if status == "OK":
        return "READY"
    if status in {"AUTH_FAILED", "PLAN_LIMITED"}:
        return "KEY_OR_PLAN_ATTENTION_REQUIRED"
    if status == "RATE_LIMITED":
        return "RATE_LIMITED"
    if status in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP"}:
        return "PENDING_SETUP"
    if status in {"NOT_CHECKED", "SKIPPED_NO_NETWORK"}:
        return "CONFIGURED_NOT_CHECKED" if configured else "NOT_CHECKED"
    return "DEGRADED"


def _readiness_tier(*, setup_status: str, freshness_class: str) -> str:
    if setup_status == "POLICY_BLOCKED":
        return "BLOCKED"
    if setup_status in {"MISSING_OPTIONAL_SECRET", "KEY_OR_PLAN_ATTENTION_REQUIRED", "RATE_LIMITED", "DEGRADED"}:
        return "ACTION_REQUIRED"
    if freshness_class == "STALE":
        return "STALE"
    if setup_status == "READY" and freshness_class == "FRESH":
        return "READY"
    return "OBSERVE"


def build_ui_provider_setup_payload(
    *,
    repo_root: Path | None = None,
    env: Mapping[str, str] | None = None,
    generated_at_utc: datetime | None = None,
) -> dict[str, Any]:
    """Build a secret-safe operator console payload for provider setup and freshness.

    The function only reads process env and an optional samples manifest; it does not
    call provider networks and never serializes secret values.
    """
    root = repo_root or Path.cwd()
    environ = env or os.environ
    now = (generated_at_utc or datetime.now(timezone.utc)).astimezone(timezone.utc)
    max_age = _parse_positive_int(
        environ.get("STRATEGY_VALIDATOR_PROVIDER_FRESHNESS_MAX_AGE_SECONDS"),
        _DEFAULT_FRESHNESS_MAX_AGE_SECONDS,
    )
    snap = build_provider_health_snapshot(env=environ, repo_root=root, generated_at_utc=now)
    capabilities = capability_by_provider_id()

    entries: list[ProviderSetupEntry] = []
    counts = {
        "provider_count": 0,
        "ready_count": 0,
        "blocked_count": 0,
        "action_required_count": 0,
        "stale_count": 0,
        "not_checked_count": 0,
        "missing_secret_count": 0,
        "public_no_signup_count": 0,
        "keyed_provider_count": 0,
        "pit_strong_count": 0,
        "canonical_status_counts": {},
    }

    for health in snap.entries:
        cap = capabilities.get(health.provider_id)
        if cap is None:
            continue
        age = _freshness_age_seconds(health.freshness_timestamp or health.last_checked_utc, now)
        freshness = _freshness_class(
            classified_status=health.classified_status,
            age_seconds=age,
            max_age_seconds=max_age,
        )
        blockers = tuple(health.blockers)
        warnings = tuple(health.warnings)
        remediation = list(health.remediation)
        if cap.requires_secret and not health.configured:
            missing_names = ", ".join(cap.env_vars) or "provider key"
            remediation.append(f"Configure one of: {missing_names} in a gitignored env file if this provider is needed.")
        if freshness == "STALE":
            remediation.append("Refresh or regenerate the provider samples manifest before relying on this feed.")
        if freshness == "NOT_CHECKED":
            remediation.append("Run the provider sample/ingestion CLI when network access and keys are available.")

        setup = _setup_status(
            requires_secret=cap.requires_secret,
            configured=health.configured,
            classified_status=health.classified_status,
            blockers=blockers,
        )
        tier = _readiness_tier(setup_status=setup, freshness_class=freshness)
        canonical_status = _canonical_status(
            requires_secret=cap.requires_secret,
            configured=health.configured,
            classified_status=health.classified_status,
            blockers=blockers,
            freshness_class=freshness,
        )
        entry = ProviderSetupEntry(
            provider_id=cap.provider_id,
            display_name=cap.display_name,
            category=cap.category.value,
            research_role=cap.research_role,
            access_type=cap.access_type.value,
            trust_level=cap.default_trust_level.value,
            pit_suitability=cap.pit_suitability.value,
            recommended_priority=cap.recommended_priority,
            official_docs_url=cap.official_docs_url,
            signup_url=cap.signup_url,
            expected_env_vars=cap.env_vars,
            requires_secret=cap.requires_secret,
            configured=health.configured,
            reachable=health.reachable,
            classified_status=health.classified_status,
            canonical_status=canonical_status,
            setup_status=setup,
            readiness_tier=tier,
            freshness_class=freshness,
            freshness_age_seconds=age,
            freshness_max_age_seconds=max_age,
            last_checked_utc=health.last_checked_utc,
            sample_digest_prefix=health.sample_digest_prefix,
            evidence_reference=health.evidence_reference,
            may_gate_live_promotion=health.may_gate_live_promotion,
            unsafe_as_promotion_authority_without_license=cap.unsafe_as_promotion_authority_without_license,
            warnings=warnings,
            blockers=blockers,
            remediation=tuple(dict.fromkeys(remediation)),
        )
        entries.append(entry)

        counts["provider_count"] += 1
        if entry.readiness_tier == "READY":
            counts["ready_count"] += 1
        if entry.readiness_tier == "BLOCKED":
            counts["blocked_count"] += 1
        if entry.readiness_tier == "ACTION_REQUIRED":
            counts["action_required_count"] += 1
        if entry.freshness_class == "STALE":
            counts["stale_count"] += 1
        if entry.freshness_class == "NOT_CHECKED":
            counts["not_checked_count"] += 1
        if entry.requires_secret and not entry.configured:
            counts["missing_secret_count"] += 1
        if entry.access_type == "PUBLIC_NO_SIGNUP":
            counts["public_no_signup_count"] += 1
        else:
            counts["keyed_provider_count"] += 1
        if entry.pit_suitability == "STRONG_PIT_SOURCE":
            counts["pit_strong_count"] += 1
        counts["canonical_status_counts"][canonical_status] = (
            int(counts["canonical_status_counts"].get(canonical_status, 0)) + 1
        )

    entries.sort(key=lambda e: (e.readiness_tier != "BLOCKED", e.recommended_priority, e.provider_id))
    payload = ProviderSetupConsolePayload(
        generated_at_utc=now.isoformat(),
        freshness_max_age_seconds=max_age,
        samples_manifest_path=snap.samples_manifest_path,
        samples_manifest_digest_prefix=snap.samples_manifest_digest_prefix,
        execution_workflow_blockers=snap.execution_workflow_blockers,
        summary={
            **counts,
            "sample_manifest_present": bool(snap.summary.get("sample_manifest_present")),
            "health_schema_version": snap.schema_version,
        },
        entries=tuple(entries),
    )
    return payload.model_dump(mode="json")


__all__ = ["build_ui_provider_setup_payload"]
