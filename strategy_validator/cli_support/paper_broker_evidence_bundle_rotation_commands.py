"""Paper broker evidence bundle rotation commands for the paper broker CLI.

This phase module keeps command bodies small while resolving runtime
dependencies through ``strategy_validator.cli.paper_broker`` so the
legacy monkeypatch surface remains stable.
"""
from __future__ import annotations

from typing import Any


_COMMANDS = frozenset(('recommend-evidence-bundle-rotation', 'run-evidence-bundle-rotation',))


def handle(ns: Any, env: dict[str, str]) -> int | None:
    if ns.cmd not in _COMMANDS:
        return None
    from strategy_validator.cli import paper_broker as _paper_broker
    json = _paper_broker.json
    sys = _paper_broker.sys
    Path = _paper_broker.Path
    dry_run_paper_order = _paper_broker.dry_run_paper_order
    get_alpaca_paper_account = _paper_broker.get_alpaca_paper_account
    get_alpaca_paper_order_status = _paper_broker.get_alpaca_paper_order_status
    list_alpaca_paper_positions = _paper_broker.list_alpaca_paper_positions
    submit_paper_order = _paper_broker.submit_paper_order
    build_paper_broker_status_artifact = _paper_broker.build_paper_broker_status_artifact
    write_paper_broker_status_artifact = _paper_broker.write_paper_broker_status_artifact
    write_paper_execution_evidence_bundle_artifact = _paper_broker.write_paper_execution_evidence_bundle_artifact
    write_paper_execution_evidence_bundle_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_verification_artifact
    write_paper_execution_evidence_bundle_drift_artifact = _paper_broker.write_paper_execution_evidence_bundle_drift_artifact
    write_paper_execution_evidence_bundle_rotation_artifact = _paper_broker.write_paper_execution_evidence_bundle_rotation_artifact
    write_paper_execution_evidence_bundle_rotation_execution_artifact = _paper_broker.write_paper_execution_evidence_bundle_rotation_execution_artifact
    write_paper_execution_evidence_bundle_attestation_artifact = _paper_broker.write_paper_execution_evidence_bundle_attestation_artifact
    write_paper_execution_evidence_bundle_attestation_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_attestation_verification_artifact
    write_paper_execution_evidence_bundle_closure_artifact = _paper_broker.write_paper_execution_evidence_bundle_closure_artifact
    write_paper_execution_evidence_bundle_closure_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_closure_verification_artifact
    write_paper_execution_evidence_bundle_export_manifest_artifact = _paper_broker.write_paper_execution_evidence_bundle_export_manifest_artifact
    write_paper_execution_evidence_bundle_export_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_export_verification_artifact
    write_paper_execution_evidence_bundle_retention_receipt_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_receipt_artifact
    write_paper_execution_evidence_bundle_retention_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_verification_artifact
    write_paper_execution_evidence_bundle_retention_signoff_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_signoff_artifact
    write_paper_execution_evidence_bundle_retention_signoff_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_signoff_verification_artifact
    write_paper_execution_evidence_bundle_retention_handoff_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_handoff_artifact
    write_paper_execution_evidence_bundle_retention_handoff_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_handoff_verification_artifact
    write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact
    write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_register_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_register_artifact
    write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_seal_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_seal_artifact
    write_paper_execution_evidence_bundle_retention_custody_seal_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_seal_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_audit_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_audit_artifact
    write_paper_execution_evidence_bundle_retention_custody_audit_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_audit_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_continuity_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_continuity_artifact
    write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_review_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_review_artifact
    write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_renewal_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_renewal_artifact
    write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_schedule_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_schedule_artifact
    write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_notice_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_notice_artifact
    write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact
    write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_completion_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_completion_artifact
    write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_closeout_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_closeout_artifact
    write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_archive_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_archive_artifact
    write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact
    write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_return_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_return_artifact
    write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact
    write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_inventory_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_inventory_artifact
    write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact
    write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_certification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_certification_artifact
    write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact
    write_paper_execution_evidence_bundle_retention_custody_attestation_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_attestation_artifact
    write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact = _paper_broker.write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact
    read_paper_execution_intent_selection_artifact = _paper_broker.read_paper_execution_intent_selection_artifact
    write_paper_execution_intent_selection_artifact = _paper_broker.write_paper_execution_intent_selection_artifact
    write_paper_order_dry_run_artifact = _paper_broker.write_paper_order_dry_run_artifact
    broker_order_id_from_submission = _paper_broker.broker_order_id_from_submission
    find_latest_submission_artifact = _paper_broker.find_latest_submission_artifact
    tracking_id_from_submission = _paper_broker.tracking_id_from_submission
    write_paper_order_status_artifact = _paper_broker.write_paper_order_status_artifact
    build_paper_submission_guard_snapshot = _paper_broker.build_paper_submission_guard_snapshot
    write_paper_order_submission_artifact = _paper_broker.write_paper_order_submission_artifact
    write_paper_account_position_snapshot_artifact = _paper_broker.write_paper_account_position_snapshot_artifact
    build_ui_paper_execution_cockpit_payload = _paper_broker.build_ui_paper_execution_cockpit_payload
    parse_env_file = _paper_broker.parse_env_file
    PaperBrokerOrderIntent = _paper_broker.PaperBrokerOrderIntent
    PaperExecutionTimelineEntry = _paper_broker.PaperExecutionTimelineEntry
    PaperExecutionTimelineSummary = _paper_broker.PaperExecutionTimelineSummary
    PaperExecutionEvidenceBundleDriftView = _paper_broker.PaperExecutionEvidenceBundleDriftView
    PaperExecutionEvidenceBundleVerificationView = _paper_broker.PaperExecutionEvidenceBundleVerificationView
    PaperExecutionEvidenceBundleView = _paper_broker.PaperExecutionEvidenceBundleView
    PaperExecutionEvidenceBundleRotationView = _paper_broker.PaperExecutionEvidenceBundleRotationView
    _paper_broker_artifact_root = _paper_broker._paper_broker_artifact_root

    if ns.cmd == "recommend-evidence-bundle-rotation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        cockpit = build_ui_paper_execution_cockpit_payload()
        timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit.get("execution_timeline_summary") or {})
        latest_bundle = cockpit.get("latest_evidence_bundle")
        latest_verification = cockpit.get("latest_evidence_bundle_verification")
        latest_drift = cockpit.get("latest_evidence_bundle_drift")
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_rotation_artifact(
            timeline_summary=timeline_summary,
            latest_evidence_bundle=PaperExecutionEvidenceBundleView.model_validate(latest_bundle) if latest_bundle else None,
            latest_evidence_bundle_verification=PaperExecutionEvidenceBundleVerificationView.model_validate(latest_verification) if latest_verification else None,
            latest_evidence_bundle_drift=PaperExecutionEvidenceBundleDriftView.model_validate(latest_drift) if latest_drift else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.rotation_status in {"NOT_NEEDED", "RECOMMENDED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "rotation_status": artifact.rotation_status,
                    "trust_banner": artifact.trust_banner,
                    "source_bundle_sha256": artifact.source_bundle_sha256,
                    "source_verification_status": artifact.source_verification_status,
                    "source_drift_status": artifact.source_drift_status,
                    "timeline_sequence_status": artifact.timeline_sequence_status,
                    "rotation_reason_codes": artifact.rotation_reason_codes,
                    "recommended_operator_sequence": artifact.recommended_operator_sequence,
                    "one_command_sequence_hint": artifact.one_command_sequence_hint,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.rotation_status in {"NOT_NEEDED", "RECOMMENDED"} else 2
    if ns.cmd == "run-evidence-bundle-rotation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        force = bool(getattr(ns, "force", False))
        cockpit = build_ui_paper_execution_cockpit_payload()
        timeline = [PaperExecutionTimelineEntry.model_validate(row) for row in cockpit.get("execution_timeline", [])]
        timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit.get("execution_timeline_summary") or {})
        latest_rotation = cockpit.get("latest_evidence_bundle_rotation")
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_rotation_execution_artifact(
            timeline=timeline,
            timeline_summary=timeline_summary,
            latest_rotation=PaperExecutionEvidenceBundleRotationView.model_validate(latest_rotation) if latest_rotation else None,
            output_root=output_root,
            force=force,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.rotation_execution_status == "PASS",
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "rotation_execution_status": artifact.rotation_execution_status,
                    "trust_banner": artifact.trust_banner,
                    "source_recommendation_status": artifact.source_recommendation_status,
                    "timeline_sequence_status": artifact.timeline_sequence_status,
                    "sealed_bundle_sha256": artifact.sealed_bundle_sha256,
                    "verification_status": artifact.verification_status,
                    "drift_status": artifact.drift_status,
                    "step_count": artifact.step_count,
                    "passed_step_count": artifact.passed_step_count,
                    "failed_step_count": artifact.failed_step_count,
                    "skipped_step_count": artifact.skipped_step_count,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.rotation_execution_status in {"PASS", "SKIPPED"} else 2
    return None
