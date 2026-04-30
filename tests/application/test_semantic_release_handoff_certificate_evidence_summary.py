from __future__ import annotations

from strategy_validator.application.research_integrity import (
    summarize_semantic_release_handoff_certificate_evidence,
)
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.core.enums import EvidenceType


def test_semantic_release_handoff_certificate_evidence_summary_blocks_invalid_evidence() -> None:
    evidence = Evidence(
        evidence_id="semantic-release-handoff-certificate-evidence-exp-1-invalid",
        experiment_id="exp-1",
        evidence_type=EvidenceType.TRIBUNAL_OPINION,
        payload={"schema_version": "semantic_release_handoff_certificate_evidence/v1"},
        source_module="strategy_validator.application.research_integrity.semantic_release_handoff_certificate",
        checksum="not-the-canonical-checksum",
    )

    summary = summarize_semantic_release_handoff_certificate_evidence(evidence)

    assert summary.schema_version == "semantic_release_handoff_certificate_evidence_summary/v1"
    assert summary.evidence_verified is False
    assert summary.handoff_allowed is False
    assert summary.recommended_action == "REBUILD_OR_BLOCK_SEMANTIC_HANDOFF_CERTIFICATE_EVIDENCE"
    assert "SEMANTIC_RELEASE_HANDOFF_CERTIFICATE_EVIDENCE_CERTIFICATE_MISSING" in summary.blocker_codes
