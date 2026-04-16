from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strategy_validator.contracts.oracle import OracleConstitutionalTrustStatus
from strategy_validator.validator.oracle_constitutional import verify_oracle_doctrine_lineage

TrustStatus = OracleConstitutionalTrustStatus


def _preferred_backing_phrase(subject: Any) -> str | None:
    source = getattr(subject, "preferred_strategic_backing_source", None)
    classification = getattr(subject, "preferred_strategic_backing_classification", None)
    exact_support = float(getattr(subject, "exact_evidence_support_score", 0.0) or 0.0)
    exact_confirm = int(getattr(subject, "exact_feedback_confirmation_count", 0) or 0)
    exact_relief = int(getattr(subject, "exact_feedback_relief_count", 0) or 0)
    if not source and not classification and exact_support <= 0.0 and exact_confirm == 0 and exact_relief == 0:
        return None
    parts: list[str] = []
    if source:
        parts.append(f"Preferred strategist backing source is `{source}`")
    if classification:
        parts.append(f"classification `{classification}`")
    if exact_support > 0.0 or exact_confirm > 0 or exact_relief > 0:
        parts.append(f"exact support `{exact_support:.2f}` with confirmations `{exact_confirm}` and relief `{exact_relief}`")
    return " with ".join(parts) + "."


@dataclass(frozen=True)
class OracleTrustBanner:
    trust_status: TrustStatus
    lineage_reason: str


def render_oracle_trust_banner(banner: OracleTrustBanner) -> str:
    return "\n".join([
        "> [!IMPORTANT]",
        f"> Trust banner: `{banner.trust_status}`",
        f"> Lineage reason: {banner.lineage_reason}",
        "",
    ])



def infer_repo_root_from_artifact_path(path: Path | None) -> Path | None:
    if path is None:
        return None
    resolved = path.resolve()
    for candidate in (resolved.parent, *resolved.parents):
        artifacts_root = candidate / "docs" / "artifacts"
        if artifacts_root.exists():
            return candidate
    return None



def maybe_verify_oracle_lineage(*, repo_root: Path | None, search_root: Path | None = None) -> Any | None:
    if repo_root is None:
        return None
    resolved_repo_root = repo_root.resolve()
    resolved_search_root = (search_root or (resolved_repo_root / "docs" / "artifacts")).resolve()
    if not resolved_search_root.exists():
        return None
    return verify_oracle_doctrine_lineage(repo_root=resolved_repo_root, search_root=resolved_search_root)



def trust_banner_for_derived_view(report: Any, lineage_verification: Any | None = None) -> OracleTrustBanner:
    evidence_gap_count = int(getattr(report, "evidence_gap_count", 0) or 0)
    if evidence_gap_count > 0:
        reason = "The Oracle Event Log window contains evidence gaps or unverifiable entries, so the derived view is not trustworthy."
        if lineage_verification is not None:
            reason = f"{reason} {trust_banner_for_lineage_verification(lineage_verification).lineage_reason}"
        return OracleTrustBanner(
            trust_status="UNTRUSTED",
            lineage_reason=reason,
        )
    if lineage_verification is None:
        return OracleTrustBanner(
            trust_status="TRUST_RESTRICTED",
            lineage_reason="Derived directly from the canonical Oracle Event Log, but doctrine-ladder lineage sealing is not available in this local render context.",
        )
    lineage_banner = trust_banner_for_lineage_verification(lineage_verification)
    if lineage_banner.trust_status == "TRUSTED":
        return OracleTrustBanner(
            trust_status="TRUSTED",
            lineage_reason=f"Derived directly from the canonical Oracle Event Log with a fully sealed doctrine lineage. {lineage_banner.lineage_reason}",
        )
    if lineage_banner.trust_status == "TRUST_RESTRICTED":
        return OracleTrustBanner(
            trust_status="TRUST_RESTRICTED",
            lineage_reason=f"Derived directly from the canonical Oracle Event Log and replayable under the current doctrine lineage posture. {lineage_banner.lineage_reason}",
        )
    return OracleTrustBanner(
        trust_status="UNTRUSTED",
        lineage_reason=f"Derived directly from the canonical Oracle Event Log, but doctrine lineage verification is below replayable trust. {lineage_banner.lineage_reason}",
    )



def trust_banner_for_event_checkpoint(manifest: Any, verification: Any, lineage_verification: Any | None = None) -> OracleTrustBanner:
    status = getattr(verification, "status", "UNVERIFIED")
    if status != "VERIFIED":
        reason = f"Checkpoint evidence verification is {status}, so the frozen view is not trustworthy."
        if lineage_verification is not None:
            reason = f"{reason} {trust_banner_for_lineage_verification(lineage_verification).lineage_reason}"
        return OracleTrustBanner(
            trust_status="UNTRUSTED",
            lineage_reason=reason,
        )
    if lineage_verification is None:
        return OracleTrustBanner(
            trust_status="TRUST_RESTRICTED",
            lineage_reason="Checkpoint artifacts verified successfully, but doctrine lineage sealing is not available in this checkpoint render context.",
        )
    lineage_banner = trust_banner_for_lineage_verification(lineage_verification)
    if lineage_banner.trust_status == "TRUSTED":
        return OracleTrustBanner(
            trust_status="TRUSTED",
            lineage_reason=f"Checkpoint artifacts verified successfully and the surrounding doctrine lineage is fully sealed. {lineage_banner.lineage_reason}",
        )
    if lineage_banner.trust_status == "TRUST_RESTRICTED":
        return OracleTrustBanner(
            trust_status="TRUST_RESTRICTED",
            lineage_reason=f"Checkpoint artifacts verified successfully and remain constitutionally replayable under the current doctrine lineage posture. {lineage_banner.lineage_reason}",
        )
    return OracleTrustBanner(
        trust_status="UNTRUSTED",
        lineage_reason=f"Checkpoint artifacts verified successfully, but doctrine lineage verification is below replayable trust. {lineage_banner.lineage_reason}",
    )



def trust_banner_for_lineage_verification(verification: Any) -> OracleTrustBanner:
    seal_status = getattr(verification, "seal_status", "ADVISORY_ONLY_INCOMPLETE")
    if seal_status == "FULLY_SEALED":
        trust_status: TrustStatus = "TRUSTED"
    elif seal_status == "CONSTITUTIONALLY_REPLAYABLE":
        trust_status = "TRUST_RESTRICTED"
    else:
        trust_status = "UNTRUSTED"
    reason = f"Observed doctrine-lineage seal status is {seal_status} with completeness {getattr(verification, 'completeness_percent', 0)}%."
    backing_phrase = _preferred_backing_phrase(verification)
    if backing_phrase:
        reason = f"{reason} {backing_phrase}"
    return OracleTrustBanner(
        trust_status=trust_status,
        lineage_reason=reason,
    )



def trust_banner_for_constitutional_gate(report: Any) -> OracleTrustBanner:
    blocking_reasons = list(getattr(report, "blocking_reasons", []) or [])
    if blocking_reasons:
        reason = blocking_reasons[0]
    else:
        reason = (
            f"Lineage seal {getattr(report, 'lineage_seal_status', 'unknown')} satisfies the minimum threshold "
            f"{getattr(report, 'minimum_required_seal_status', 'unknown')} and the constitutional evidence manifest verified successfully."
        )
    backing_phrase = _preferred_backing_phrase(report)
    if backing_phrase:
        reason = f"{reason} {backing_phrase}"
    return OracleTrustBanner(
        trust_status=getattr(report, "trust_status", "UNTRUSTED"),
        lineage_reason=reason,
    )



def trust_banner_for_legacy_surface(*, legacy_surface: str, report: Any, lineage_verification: Any | None = None) -> OracleTrustBanner:
    if lineage_verification is not None:
        lineage_banner = trust_banner_for_lineage_verification(lineage_verification)
        if getattr(report, "doctrine_posture", None) == "REPAIR_FIRST" or getattr(report, "derived_classification", None) == "EVIDENCE_GAP":
            return OracleTrustBanner(
                trust_status="UNTRUSTED",
                lineage_reason=f"Legacy compatibility surface `{legacy_surface}` is reporting an evidence gap or repair-first posture. {lineage_banner.lineage_reason}",
            )
        return OracleTrustBanner(
            trust_status=lineage_banner.trust_status if lineage_banner.trust_status != "TRUSTED" else "TRUST_RESTRICTED",
            lineage_reason=f"Legacy compatibility surface `{legacy_surface}` remains replay-safe only through the canonical Oracle Event Log and doctrine lineage gate. {lineage_banner.lineage_reason}",
        )

    if getattr(report, "doctrine_posture", None) == "REPAIR_FIRST" or getattr(report, "derived_classification", None) == "EVIDENCE_GAP":
        return OracleTrustBanner(
            trust_status="UNTRUSTED",
            lineage_reason=f"Legacy compatibility surface `{legacy_surface}` is carrying an evidence gap or repair-first posture without validated lineage context.",
        )
    return OracleTrustBanner(
        trust_status="TRUST_RESTRICTED",
        lineage_reason=f"Legacy compatibility surface `{legacy_surface}` is preserved for replay, but the canonical Oracle Event Log remains the primary trust surface.",
    )
