from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
COCKPIT = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit.py"
RUNTIME = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_runtime.py"
RECOMMENDATIONS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_recommendations.py"


def test_paper_execution_cockpit_keeps_lazy_registry_out_of_public_builder_module() -> None:
    source = COCKPIT.read_text(encoding="utf-8")

    assert "lazy_callable(" not in source
    assert "lazy_model(" not in source
    assert "paper_execution_cockpit_runtime import *" in source

    runtime_source = RUNTIME.read_text(encoding="utf-8")
    assert runtime_source.count("lazy_callable(") >= 50
    assert runtime_source.count("lazy_model(") >= 50
    assert "build_ui_paper_execution_cockpit_payload" not in runtime_source


def test_paper_execution_cockpit_recommendation_synthesis_is_extracted() -> None:
    cockpit_source = COCKPIT.read_text(encoding="utf-8")
    recommendations_source = RECOMMENDATIONS.read_text(encoding="utf-8")

    assert "def _recommended_actions(" not in cockpit_source
    assert "paper_execution_cockpit_recommendations import _recommended_actions" in cockpit_source
    assert "def _recommended_actions(" in recommendations_source
    assert "Resolve paper broker policy blockers" in recommendations_source

EXECUTION_STATE = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_state.py"
EXECUTION_COMMON = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_common.py"
EXECUTION_INTENT = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_intent.py"
EXECUTION_JOURNAL = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_journal.py"
EXECUTION_FRESHNESS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_freshness.py"
EXECUTION_TIMELINE = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_execution_timeline.py"


def test_paper_execution_cockpit_execution_state_is_extracted() -> None:
    cockpit_source = COCKPIT.read_text(encoding="utf-8")
    execution_state_source = EXECUTION_STATE.read_text(encoding="utf-8")

    assert "def _journal_entries(" not in cockpit_source
    assert "def _submission_receipts(" not in cockpit_source
    assert "def _freshness_gate(" not in cockpit_source
    assert "def _execution_timeline(" not in cockpit_source
    assert "paper_execution_cockpit_execution_state import" in cockpit_source

    assert "paper_execution_cockpit_execution_journal import" in execution_state_source
    assert "paper_execution_cockpit_execution_freshness import" in execution_state_source
    assert "paper_execution_cockpit_execution_timeline import" in execution_state_source
    assert "def _journal_entries(" not in execution_state_source
    assert "def _submission_receipts(" not in execution_state_source
    assert "def _freshness_gate(" not in execution_state_source
    assert "def _execution_timeline(" not in execution_state_source


def test_paper_execution_cockpit_execution_state_is_phase_decomposed() -> None:
    common_source = EXECUTION_COMMON.read_text(encoding="utf-8")
    intent_source = EXECUTION_INTENT.read_text(encoding="utf-8")
    journal_source = EXECUTION_JOURNAL.read_text(encoding="utf-8")
    freshness_source = EXECUTION_FRESHNESS.read_text(encoding="utf-8")
    timeline_source = EXECUTION_TIMELINE.read_text(encoding="utf-8")

    assert "def _safe_read_json(" in common_source
    assert "def _build_intent_preview(" in intent_source
    assert "def _dry_run(" in intent_source
    assert "def _journal_entries(" in journal_source
    assert "def _submission_receipts(" in journal_source
    assert "def _freshness_gate(" in freshness_source
    assert "def _selected_dry_run_replay_status(" in freshness_source
    assert "def _execution_timeline(" in timeline_source
    assert "PaperExecutionTimelineSummary" in timeline_source

EVIDENCE_LIFECYCLE = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle.py"


def test_paper_execution_cockpit_evidence_lifecycle_is_extracted() -> None:
    cockpit_source = COCKPIT.read_text(encoding="utf-8")
    lifecycle_source = EVIDENCE_LIFECYCLE.read_text(encoding="utf-8")

    assert "def _attestation_view_from_artifact(" not in cockpit_source
    assert "read_paper_execution_evidence_bundle_views(repo_root=repo_root)" not in cockpit_source
    assert "build_paper_execution_evidence_lifecycle_projection(" in cockpit_source
    assert "**evidence_lifecycle.summary_kwargs" in cockpit_source
    assert "**evidence_lifecycle.action_kwargs" in cockpit_source
    assert "**evidence_lifecycle.payload_kwargs" in cockpit_source

    assert "def _attestation_view_from_artifact(" in lifecycle_source
    assert "def build_paper_execution_evidence_lifecycle_projection(" in lifecycle_source
    assert "read_paper_execution_evidence_bundle_views(repo_root=repo_root)" in lifecycle_source
    assert "PaperExecutionEvidenceLifecycleProjection" in lifecycle_source

EVIDENCE_LIFECYCLE_PAYLOADS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle_payloads.py"
EVIDENCE_LIFECYCLE_KEYS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle_keys.py"
EVIDENCE_LIFECYCLE_SUMMARY_PAYLOADS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle_summary_payloads.py"
EVIDENCE_LIFECYCLE_ACTION_PAYLOADS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle_action_payloads.py"
EVIDENCE_LIFECYCLE_VALUE_PAYLOADS = REPO_ROOT / "strategy_validator/application/paper_execution_cockpit_evidence_lifecycle_value_payloads.py"


def test_paper_execution_cockpit_evidence_lifecycle_payload_assembly_is_extracted() -> None:
    lifecycle_source = EVIDENCE_LIFECYCLE.read_text(encoding="utf-8")
    payloads_source = EVIDENCE_LIFECYCLE_PAYLOADS.read_text(encoding="utf-8")
    keys_source = EVIDENCE_LIFECYCLE_KEYS.read_text(encoding="utf-8")
    summary_source = EVIDENCE_LIFECYCLE_SUMMARY_PAYLOADS.read_text(encoding="utf-8")
    action_source = EVIDENCE_LIFECYCLE_ACTION_PAYLOADS.read_text(encoding="utf-8")
    value_source = EVIDENCE_LIFECYCLE_VALUE_PAYLOADS.read_text(encoding="utf-8")

    assert "summary_kwargs = {" not in lifecycle_source
    assert "action_kwargs = {" not in lifecycle_source
    assert "payload_kwargs = {" not in lifecycle_source
    assert "build_evidence_lifecycle_summary_kwargs(values)" in lifecycle_source
    assert "build_evidence_lifecycle_action_kwargs(values)" in lifecycle_source
    assert "build_evidence_lifecycle_payload_kwargs(values)" in lifecycle_source

    assert "def build_evidence_lifecycle_summary_kwargs(" not in payloads_source
    assert "def build_evidence_lifecycle_action_kwargs(" not in payloads_source
    assert "def build_evidence_lifecycle_payload_kwargs(" not in payloads_source
    assert "paper_execution_cockpit_evidence_lifecycle_summary_payloads import" in payloads_source
    assert "paper_execution_cockpit_evidence_lifecycle_action_payloads import" in payloads_source
    assert "paper_execution_cockpit_evidence_lifecycle_value_payloads import" in payloads_source

    assert "_VALUE_KEYS = (" in keys_source
    assert "_require_complete_values" in keys_source
    assert "def build_evidence_lifecycle_summary_kwargs(" in summary_source
    assert "latest_evidence_bundle_retention_custody_attestation_verification_due_at_utc" in summary_source
    assert "def build_evidence_lifecycle_action_kwargs(" in action_source
    assert "def build_evidence_lifecycle_payload_kwargs(" in value_source
    assert "return {key: values[key] for key in _VALUE_KEYS}" in value_source
