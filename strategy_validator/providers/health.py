"""Build provider health snapshots from registry + optional env + optional samples manifest."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from strategy_validator.contracts.provider_capabilities import (
    ProviderAccessType,
    all_provider_capabilities,
)
from strategy_validator.contracts.provider_health import ProviderHealthEntry, ProviderHealthSnapshot


def _truthy(raw: str | None) -> bool:
    if raw is None:
        return False
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _configured_from_env(env: Mapping[str, str], names: tuple[str, ...]) -> bool:
    for name in names:
        raw = env.get(name, "").strip()
        if raw and raw.upper() not in {"CHANGEME", "REPLACE_ME", "YOUR_KEY_HERE"}:
            return True
    return False


def _alpaca_execution_blockers(env: Mapping[str, str]) -> tuple[str, ...]:
    issues: list[str] = []
    mode = (env.get("ALPACA_TRADING_MODE") or "").strip().lower()
    base = (env.get("ALPACA_BASE_URL") or "").strip().lower()
    personal = _truthy(env.get("PERSONAL_LIVE_APPROVED")) or _truthy(
        env.get("STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED")
    )
    if mode == "live" and not personal:
        issues.append("alpaca_live_without_personal_live_approval")
    if "api.alpaca.markets" in base and "paper" not in base and not personal:
        issues.append("alpaca_live_base_url_without_personal_live_approval")
    return tuple(issues)


def _safe_manifest_path(raw: str | None, repo_root: Path | None) -> Path | None:
    if not raw or not raw.strip():
        return None
    p = Path(raw.strip())
    if not p.is_absolute() and repo_root is not None:
        p = (repo_root / p).resolve()
    else:
        p = p.resolve()
    if repo_root is not None:
        try:
            p.relative_to(repo_root.resolve())
        except ValueError:
            return None
    return p if p.is_file() else None


def _load_sample_rows(path: Path | None) -> dict[str, dict[str, Any]]:
    if path is None or not path.is_file():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    rows: dict[str, dict[str, Any]] = {}
    for entry in data.get("entries", []):
        pid = entry.get("provider_id")
        if isinstance(pid, str):
            rows[pid] = entry
    return rows


def _manifest_digest_prefix(path: Path | None) -> str | None:
    if path is None or not path.is_file():
        return None
    h = hashlib.sha256(path.read_bytes()).hexdigest()
    return h[:16]


def build_provider_health_snapshot(
    *,
    env: Mapping[str, str],
    samples_manifest_path: Path | None = None,
    repo_root: Path | None = None,
    generated_at_utc: datetime | None = None,
) -> ProviderHealthSnapshot:
    """Assemble health snapshot. Missing manifest yields NOT_CHECKED / unreachable for samples."""
    when = (generated_at_utc or datetime.now(timezone.utc)).isoformat()
    manifest_path = samples_manifest_path
    if manifest_path is None:
        manifest_path = _safe_manifest_path(env.get("STRATEGY_VALIDATOR_PROVIDER_SAMPLES_MANIFEST"), repo_root)
    sample_rows = _load_sample_rows(manifest_path)
    digest_prefix = _manifest_digest_prefix(manifest_path)

    exec_blockers = _alpaca_execution_blockers(env)
    entries: list[ProviderHealthEntry] = []

    ok_n = pending_n = issue_n = 0
    for cap in sorted(all_provider_capabilities(), key=lambda p: p.provider_id):
        row = sample_rows.get(cap.provider_id, {})
        classified = str(row.get("classified_status", "NOT_CHECKED"))
        http_raw = row.get("http_status")
        if isinstance(http_raw, int):
            http_status: int | None = http_raw
        elif isinstance(http_raw, str) and http_raw.strip().isdigit():
            http_status = int(http_raw.strip())
        else:
            http_status = None
        sha = row.get("sha256")
        digest_p = str(sha)[:16] if isinstance(sha, str) and len(sha) >= 16 else None

        if cap.access_type == ProviderAccessType.PUBLIC_NO_SIGNUP:
            configured = True
        elif cap.access_type == ProviderAccessType.BROKER_ACCOUNT_REQUIRED:
            configured = _configured_from_env(env, cap.env_vars)
        else:
            configured = _configured_from_env(env, cap.env_vars)

        reachable = classified == "OK" and http_status == 200
        if classified == "OK" and http_status == 200:
            ok_n += 1
        elif classified in {"PENDING_KEY", "PENDING_MANUAL_BROKER_SETUP", "SKIPPED_NO_NETWORK"}:
            pending_n += 1
        elif classified not in {"NOT_CHECKED"}:
            issue_n += 1

        blockers: list[str] = []
        warnings: list[str] = []
        remediation: list[str] = []

        if cap.requires_secret and not configured:
            warnings.append("optional_provider_not_configured")
            remediation.append(f"Add a key for {cap.display_name} to a gitignored env file if needed.")
        if classified in {"AUTH_FAILED", "PLAN_LIMITED"}:
            remediation.append("Verify API key tier and provider dashboard status.")
        if classified == "RATE_LIMITED":
            remediation.append("Backoff or upgrade plan; sample retrieval is rate-limited.")
        if cap.provider_id == "alpaca" and exec_blockers:
            blockers.extend(list(exec_blockers))
            remediation.append("Keep ALPACA_TRADING_MODE=paper unless PERSONAL_LIVE_APPROVED=true.")

        freshness = row.get("retrieved_at_utc") if isinstance(row.get("retrieved_at_utc"), str) else None
        ev_ref = ""
        if manifest_path and cap.provider_id in sample_rows:
            ev_ref = f"{manifest_path.as_posix()}#provider_id={cap.provider_id}"

        execution_posture: dict[str, Any] | None = None
        if cap.provider_id == "alpaca":
            mode = (env.get("ALPACA_TRADING_MODE") or "").strip().lower()
            personal = _truthy(env.get("PERSONAL_LIVE_APPROVED")) or _truthy(
                env.get("STRATEGY_VALIDATOR_PERSONAL_LIVE_APPROVED")
            )
            base = (env.get("ALPACA_BASE_URL") or "").strip().lower()
            paper_live_warnings: list[str] = []
            if mode == "live" and not personal:
                paper_live_warnings.append("live_mode_without_personal_live_approval")
            if "api.alpaca.markets" in base and "paper" not in base and not personal:
                paper_live_warnings.append("live_api_base_without_personal_live_approval")
            execution_posture = {
                "trading_mode": mode or None,
                "personal_live_approved": personal,
                "paper_live_warnings": paper_live_warnings,
                "execution_policy_blockers": list(exec_blockers),
                "execution_authority": "BLOCKED_BY_POLICY" if exec_blockers else "NOT_BLOCKED_BY_POLICY",
            }

        entries.append(
            ProviderHealthEntry(
                provider_id=cap.provider_id,
                display_name=cap.display_name,
                configured=configured,
                reachable=reachable,
                classified_status=classified,
                http_status=http_status,
                access_type=cap.access_type.value,
                trust_level=cap.default_trust_level.value,
                pit_suitability=cap.pit_suitability.value,
                last_checked_utc=freshness or when,
                sample_digest_prefix=digest_p,
                freshness_timestamp=freshness,
                may_gate_live_promotion=cap.may_gate_live_promotion,
                blockers=tuple(blockers),
                warnings=tuple(warnings),
                remediation=tuple(remediation),
                evidence_reference=ev_ref,
                execution_posture=execution_posture,
            )
        )

    summary = {
        "provider_count": len(entries),
        "sample_manifest_present": manifest_path is not None and manifest_path.is_file(),
        "classified_ok_count": ok_n,
        "pending_or_stub_count": pending_n,
        "non_ok_checked_count": issue_n,
    }

    return ProviderHealthSnapshot(
        generated_at_utc=when,
        samples_manifest_path=manifest_path.as_posix() if manifest_path else None,
        samples_manifest_digest_prefix=digest_prefix,
        execution_workflow_blockers=exec_blockers,
        entries=tuple(entries),
        summary=summary,
    )


def provider_health_snapshot_public_payload(snap: ProviderHealthSnapshot) -> dict[str, Any]:
    """Serialize snapshot for HTTP read-plane routes; omit null ``execution_posture`` per entry (Alpaca-only)."""
    payload = snap.model_dump(mode="json")
    raw_entries = payload.get("entries")
    if isinstance(raw_entries, list):
        for ent in raw_entries:
            if isinstance(ent, dict) and ent.get("execution_posture") is None:
                ent.pop("execution_posture", None)
    return payload


def build_provider_research_spine_addon(
    *,
    env: Mapping[str, str],
    repo_root: Path | None = None,
) -> dict[str, Any]:
    """Compact, readiness-safe addon dict (no large per-provider arrays)."""
    snap = build_provider_health_snapshot(env=env, repo_root=repo_root)
    return {
        "schema_version": "provider_research_spine_addon/v1",
        "snapshot_schema": snap.schema_version,
        "summary": snap.summary,
        "execution_workflow_blockers": list(snap.execution_workflow_blockers),
        "samples_manifest_digest_prefix": snap.samples_manifest_digest_prefix,
    }
