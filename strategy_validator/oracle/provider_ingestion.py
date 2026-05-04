"""Advisory provider context from evidence manifests — read-only, non-authoritative."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from strategy_validator.contracts.evidence_manifest import ProviderEvidenceManifest
from strategy_validator.contracts.oracle_provider_context import OracleProviderAdvisorySummary


def _digest_json(obj: Any) -> str:
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


def build_advisory_summary_from_evidence(
    *,
    manifest: ProviderEvidenceManifest,
    normalized_records: list[dict[str, Any]] | None = None,
) -> OracleProviderAdvisorySummary:
    """Produce advisory summary for Oracle surfaces. Does not read ledger or mutate state."""
    manifest_dump = manifest.model_dump(mode="json")
    digest = _digest_json(manifest_dump)

    coverage = {
        "artifact_count": len(manifest.artifacts),
        "trust_summary": manifest.trust_summary,
        "pit_summary": manifest.pit_summary,
    }
    gaps: list[str] = []
    if not manifest.provider_sample_manifest_digest:
        gaps.append("missing_provider_sample_manifest_digest")
    if manifest.unavailable_providers:
        gaps.append("providers_with_auth_or_plan_issues")

    pit_warnings: list[str] = []
    if manifest.pit_summary:
        pit_warnings.append("freemium_and_snapshot_providers_are_not_canonical_pit_authority")
    if normalized_records:
        for row in normalized_records:
            if not row.get("may_be_used_for_validation", False):
                pit_warnings.append(f"validation_not_advised:{row.get('provider_id', '?')}")

    return OracleProviderAdvisorySummary(
        evidence_manifest_digest=digest,
        provider_coverage=coverage,
        freshness_gaps=tuple(gaps),
        unavailable_providers=tuple(manifest.unavailable_providers),
        pit_trust_warnings=tuple(pit_warnings),
        macro_context_hints=("macro_samples_require_release_timestamp_discipline",),
        market_data_context_hints=("market_samples_are_not_exchange_canonical_tape",),
        news_context_hints=("news_samples_are_not_pit_safe_without_archive",),
        advisory_only=True,
        ledger_mutation_disclaimed=True,
    )


def load_evidence_manifest(path: Path) -> ProviderEvidenceManifest | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return ProviderEvidenceManifest.model_validate(data)


__all__ = ["build_advisory_summary_from_evidence", "load_evidence_manifest"]
