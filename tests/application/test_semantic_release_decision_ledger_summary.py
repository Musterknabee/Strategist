from strategy_validator.application.research_integrity import summarize_semantic_adjudication_release_decision_ledger
from strategy_validator.contracts.semantic import (
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseDecisionLedgerEntry,
)


def test_release_decision_ledger_summary_recommends_no_decision_for_empty_ledger() -> None:
    ledger = SemanticAdjudicationReleaseDecisionLedger(
        ledger_id="semantic-release-decision-ledger-empty",
        experiment_id="none",
        entry_count=0,
        accepted_decision_count=0,
        blocked_decision_count=0,
        terminal_recommended_action="NO_SEMANTIC_RELEASE_DECISIONS_RECORDED",
        entries=[],
        payload_checksum="pending",
    )
    # Preserve the intentionally invalid checksum to exercise summary failure posture.
    summary = summarize_semantic_adjudication_release_decision_ledger(ledger)
    assert summary.schema_version == "semantic_adjudication_release_decision_ledger_summary/v1"
    assert summary.ledger_verified is False
    assert summary.recommended_action == "REBUILD_OR_REVERIFY_SEMANTIC_RELEASE_DECISION_LEDGER"
    assert "SEMANTIC_RELEASE_DECISION_LEDGER_CHECKSUM_MISMATCH" in summary.ledger_issue_codes


def test_release_decision_ledger_summary_terminal_fields_are_operator_readable() -> None:
    entry = SemanticAdjudicationReleaseDecisionLedgerEntry(
        entry_index=0,
        decision_id="decision-1",
        capsule_id="capsule-1",
        index_id="index-1",
        bundle_id="bundle-1",
        experiment_id="exp-1",
        decision="BLOCK_ADJUDICATION",
        decision_allowed=False,
        decided_by="ci",
        decision_payload_checksum="abc",
        previous_entry_checksum=None,
        entry_checksum="bad",
    )
    ledger = SemanticAdjudicationReleaseDecisionLedger(
        ledger_id="ledger-1",
        experiment_id="exp-1",
        entry_count=1,
        accepted_decision_count=0,
        blocked_decision_count=1,
        terminal_recommended_action="RESPECT_TERMINAL_BLOCK_OR_REBUILD_DECISION",
        entries=[entry],
        payload_checksum="bad",
    )
    summary = summarize_semantic_adjudication_release_decision_ledger(ledger)
    assert summary.terminal_decision_id == "decision-1"
    assert summary.terminal_decision == "BLOCK_ADJUDICATION"
    assert summary.terminal_decision_allowed is False
