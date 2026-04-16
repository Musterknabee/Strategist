from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from strategy_validator.contracts.oracle import (
    OracleArtifactCoverageStatus,
    OracleArtifactIntegrityStatus,
    OracleConstitutionalTrustStatus,
    OracleSupportChainRemediationStatus,
    OracleSupportVerificationStatus,
)


@dataclass(frozen=True)
class OracleTrustPlaneAssessment:
    trust_plane_summary_line: str
    trust_plane_actions: list[str]


def _unique(items: Iterable[str]) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        value = str(item).strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out


def assess_trust_plane(
    *,
    evidence_freshness_status: str,
    evidence_integrity_status: OracleArtifactIntegrityStatus,
    evidence_coverage_status: OracleArtifactCoverageStatus,
    support_verification_status: OracleSupportVerificationStatus,
    support_chain_trust_status: OracleConstitutionalTrustStatus,
    support_chain_remediation_status: OracleSupportChainRemediationStatus,
    support_chain_remediation_actions: list[str] | None = None,
    surface_label: str = 'this strategist surface',
) -> OracleTrustPlaneAssessment:
    trust_plane_summary_line = (
        f'Trust plane: freshness={evidence_freshness_status}; integrity={evidence_integrity_status}; '
        f'coverage={evidence_coverage_status}; verification={support_verification_status}; '
        f'trust={support_chain_trust_status}; remediation={support_chain_remediation_status}.'
    )

    actions: list[str] = []
    if support_chain_trust_status == 'TRUST_RESTRICTED':
        actions.append(f'Treat {surface_label} as trust-restricted until the listed support-chain cautions are resolved.')
    elif support_chain_trust_status == 'UNTRUSTED':
        actions.append(f'Do not materially rely on {surface_label} until the listed support-chain defects are repaired.')

    actions.extend(list(support_chain_remediation_actions or []))
    return OracleTrustPlaneAssessment(
        trust_plane_summary_line=trust_plane_summary_line,
        trust_plane_actions=_unique(actions),
    )
