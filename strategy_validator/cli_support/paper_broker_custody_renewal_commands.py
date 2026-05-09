"""Custody renewal lifecycle command handlers for paper broker retention evidence.

Handlers resolve callables through ``strategy_validator.cli.paper_broker`` at
execution time so the historical monkeypatch surface remains stable.
"""

from typing import Any


def handle(ns: Any, env: dict[str, str]) -> int | None:
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

    if ns.cmd == "renew-evidence-bundle-retention-custody":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_review_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_renewal_artifact(
            retention_custody_review_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            renewed_by=str(getattr(ns, "renewed_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            renewal_interval_days=int(getattr(ns, "renewal_interval_days", 30) or 30),
            renewal_note=str(getattr(ns, "renewal_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.renewal_status in {"RENEWED", "RENEWAL_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "renewal_status": artifact.renewal_status,
            "trust_banner": artifact.trust_banner,
            "custody_renewal_id": artifact.custody_renewal_id,
            "renewed_by": artifact.renewed_by,
            "custody_location": artifact.custody_location,
            "renewal_interval_days": artifact.renewal_interval_days,
            "source_retention_custody_review_verification_status": artifact.source_retention_custody_review_verification_status,
            "retention_custody_review_verification_artifact_hash_valid": artifact.retention_custody_review_verification_artifact_hash_valid,
            "custody_renewal_statement_sha256": artifact.custody_renewal_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.renewal_status in {"RENEWED", "RENEWAL_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-renewal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_renewal_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact(
            retention_custody_renewal_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_renewal_status": artifact.source_retention_custody_renewal_status,
            "retention_custody_renewal_artifact_hash_valid": artifact.retention_custody_renewal_artifact_hash_valid,
            "custody_renewal_statement_hash_valid": artifact.custody_renewal_statement_hash_valid,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "schedule-evidence-bundle-retention-custody-renewal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_renewal_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_schedule_artifact(
            retention_custody_renewal_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            scheduled_by=str(getattr(ns, "scheduled_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            reminder_days_before_due=int(getattr(ns, "reminder_days_before_due", 7) or 7),
            schedule_note=str(getattr(ns, "schedule_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.schedule_status in {"SCHEDULED", "SCHEDULE_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "schedule_status": artifact.schedule_status,
            "trust_banner": artifact.trust_banner,
            "custody_schedule_id": artifact.custody_schedule_id,
            "schedule_start_at_utc": artifact.schedule_start_at_utc,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "renewal_interval_days": artifact.renewal_interval_days,
            "reminder_days_before_due": artifact.reminder_days_before_due,
            "source_retention_custody_renewal_verification_status": artifact.source_retention_custody_renewal_verification_status,
            "retention_custody_renewal_verification_artifact_hash_valid": artifact.retention_custody_renewal_verification_artifact_hash_valid,
            "custody_schedule_statement_sha256": artifact.custody_schedule_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.schedule_status in {"SCHEDULED", "SCHEDULE_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-schedule":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_schedule_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact(
            retention_custody_schedule_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_schedule_status": artifact.source_retention_custody_schedule_status,
            "retention_custody_schedule_artifact_hash_valid": artifact.retention_custody_schedule_artifact_hash_valid,
            "custody_schedule_statement_hash_valid": artifact.custody_schedule_statement_hash_valid,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2


    if ns.cmd == "notice-evidence-bundle-retention-custody-renewal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_schedule_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_notice_artifact(
            retention_custody_schedule_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            notified_by=str(getattr(ns, "notified_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            notice_note=str(getattr(ns, "notice_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.notice_status in {"NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "notice_status": artifact.notice_status,
            "trust_banner": artifact.trust_banner,
            "custody_notice_id": artifact.custody_notice_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "reminder_window_starts_at_utc": artifact.reminder_window_starts_at_utc,
            "days_until_due": artifact.days_until_due,
            "source_retention_custody_schedule_verification_status": artifact.source_retention_custody_schedule_verification_status,
            "retention_custody_schedule_verification_artifact_hash_valid": artifact.retention_custody_schedule_verification_artifact_hash_valid,
            "custody_notice_statement_sha256": artifact.custody_notice_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.notice_status in {"NOTICE_DUE", "NOTICE_PENDING", "NOTICE_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-notice":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_notice_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact(
            retention_custody_notice_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_notice_status": artifact.source_retention_custody_notice_status,
            "retention_custody_notice_artifact_hash_valid": artifact.retention_custody_notice_artifact_hash_valid,
            "custody_notice_statement_hash_valid": artifact.custody_notice_statement_hash_valid,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2


    if ns.cmd == "acknowledge-evidence-bundle-retention-custody-notice":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_notice_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact(
            retention_custody_notice_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            acknowledged_by=str(getattr(ns, "acknowledged_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            acknowledgment_note=str(getattr(ns, "acknowledgment_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.acknowledgment_status in {"ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "acknowledgment_status": artifact.acknowledgment_status,
            "trust_banner": artifact.trust_banner,
            "custody_acknowledgment_id": artifact.custody_acknowledgment_id,
            "custody_notice_id": artifact.custody_notice_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "source_retention_custody_notice_verification_status": artifact.source_retention_custody_notice_verification_status,
            "retention_custody_notice_verification_artifact_hash_valid": artifact.retention_custody_notice_verification_artifact_hash_valid,
            "custody_acknowledgment_statement_sha256": artifact.custody_acknowledgment_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.acknowledgment_status in {"ACKNOWLEDGED", "ACKNOWLEDGED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-acknowledgment":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_acknowledgment_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact(
            retention_custody_acknowledgment_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_acknowledgment_status": artifact.source_retention_custody_acknowledgment_status,
            "retention_custody_acknowledgment_artifact_hash_valid": artifact.retention_custody_acknowledgment_artifact_hash_valid,
            "custody_acknowledgment_statement_hash_valid": artifact.custody_acknowledgment_statement_hash_valid,
            "custody_notice_id": artifact.custody_notice_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "complete-evidence-bundle-retention-custody-renewal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_acknowledgment_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_completion_artifact(
            retention_custody_acknowledgment_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            completed_by=str(getattr(ns, "completed_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            completion_note=str(getattr(ns, "completion_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.completion_status in {"COMPLETED", "COMPLETED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "completion_status": artifact.completion_status,
            "trust_banner": artifact.trust_banner,
            "custody_completion_id": artifact.custody_completion_id,
            "custody_acknowledgment_id": artifact.custody_acknowledgment_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "source_retention_custody_acknowledgment_verification_status": artifact.source_retention_custody_acknowledgment_verification_status,
            "retention_custody_acknowledgment_verification_artifact_hash_valid": artifact.retention_custody_acknowledgment_verification_artifact_hash_valid,
            "custody_completion_statement_sha256": artifact.custody_completion_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.completion_status in {"COMPLETED", "COMPLETED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-completion":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_completion_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact(
            retention_custody_completion_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_completion_status": artifact.source_retention_custody_completion_status,
            "retention_custody_completion_artifact_hash_valid": artifact.retention_custody_completion_artifact_hash_valid,
            "custody_completion_statement_hash_valid": artifact.custody_completion_statement_hash_valid,
            "custody_completion_id": artifact.custody_completion_id,
            "custody_acknowledgment_id": artifact.custody_acknowledgment_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "closeout-evidence-bundle-retention-custody-renewal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_completion_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_closeout_artifact(
            retention_custody_completion_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            closed_out_by=str(getattr(ns, "closed_out_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            closeout_note=str(getattr(ns, "closeout_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.closeout_status in {"CLOSED", "CLOSED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "closeout_status": artifact.closeout_status,
            "trust_banner": artifact.trust_banner,
            "custody_closeout_id": artifact.custody_closeout_id,
            "custody_completion_id": artifact.custody_completion_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "source_retention_custody_completion_verification_status": artifact.source_retention_custody_completion_verification_status,
            "retention_custody_completion_verification_artifact_hash_valid": artifact.retention_custody_completion_verification_artifact_hash_valid,
            "custody_closeout_statement_sha256": artifact.custody_closeout_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.closeout_status in {"CLOSED", "CLOSED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-closeout":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_closeout_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact(
            retention_custody_closeout_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.verification_status == "PASS",
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "verification_status": artifact.verification_status,
            "trust_banner": artifact.trust_banner,
            "source_retention_custody_closeout_status": artifact.source_retention_custody_closeout_status,
            "retention_custody_closeout_artifact_hash_valid": artifact.retention_custody_closeout_artifact_hash_valid,
            "custody_closeout_statement_hash_valid": artifact.custody_closeout_statement_hash_valid,
            "custody_closeout_id": artifact.custody_closeout_id,
            "custody_completion_id": artifact.custody_completion_id,
            "next_renewal_due_at_utc": artifact.next_renewal_due_at_utc,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    return None

