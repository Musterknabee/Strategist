"""Paper broker retention receipt signoff commands for the paper broker CLI.

This phase module keeps command bodies small while resolving runtime
dependencies through ``strategy_validator.cli.paper_broker`` so the
legacy monkeypatch surface remains stable.
"""
from __future__ import annotations

from typing import Any


_COMMANDS = frozenset(('receipt-evidence-bundle-retention', 'verify-evidence-bundle-retention', 'signoff-evidence-bundle-retention', 'verify-evidence-bundle-retention-signoff',))


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

    if ns.cmd == "receipt-evidence-bundle-retention":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_export_verification = str(getattr(ns, "export_verification_artifact", "") or "").strip()
        if raw_export_verification == ".":
            raw_export_verification = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_receipt_artifact(
            export_verification_artifact_path=Path(raw_export_verification) if raw_export_verification else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.retention_status in {"READY_FOR_RETENTION", "READY_RESTRICTED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "retention_status": artifact.retention_status,
                    "trust_banner": artifact.trust_banner,
                    "source_export_verification_artifact_sha256": artifact.source_export_verification_artifact_sha256,
                    "source_export_verification_status": artifact.source_export_verification_status,
                    "export_verification_artifact_hash_valid": artifact.export_verification_artifact_hash_valid,
                    "source_export_manifest_status": artifact.source_export_manifest_status,
                    "retained_entry_count": artifact.retained_entry_count,
                    "retained_ready_entry_count": artifact.retained_ready_entry_count,
                    "total_size_bytes": artifact.total_size_bytes,
                    "retention_index_sha256": artifact.retention_index_sha256,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.retention_status in {"READY_FOR_RETENTION", "READY_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_retention_receipt = str(getattr(ns, "retention_receipt_artifact", "") or "").strip()
        if raw_retention_receipt == ".":
            raw_retention_receipt = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_verification_artifact(
            retention_receipt_artifact_path=Path(raw_retention_receipt) if raw_retention_receipt else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.verification_status == "PASS",
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "verification_status": artifact.verification_status,
                    "trust_banner": artifact.trust_banner,
                    "source_retention_receipt_declared_sha256": artifact.source_retention_receipt_declared_sha256,
                    "source_retention_receipt_computed_sha256": artifact.source_retention_receipt_computed_sha256,
                    "source_retention_receipt_status": artifact.source_retention_receipt_status,
                    "retention_receipt_hash_valid": artifact.retention_receipt_hash_valid,
                    "retention_index_hash_valid": artifact.retention_index_hash_valid,
                    "source_retention_entry_count": artifact.source_retention_entry_count,
                    "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
                    "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
                    "missing_entry_count": artifact.missing_entry_count,
                    "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.verification_status == "PASS" else 2
    if ns.cmd == "signoff-evidence-bundle-retention":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_retention_verification = str(getattr(ns, "retention_verification_artifact", "") or "").strip()
        if raw_retention_verification == ".":
            raw_retention_verification = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_signoff_artifact(
            retention_verification_artifact_path=Path(raw_retention_verification) if raw_retention_verification else None,
            output_root=output_root,
            operator_id=str(getattr(ns, "operator_id", "operator") or "operator"),
            decision_note=str(getattr(ns, "decision_note", "") or "") or None,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.signoff_status in {"SIGNED_OFF", "SIGNED_OFF_RESTRICTED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "signoff_status": artifact.signoff_status,
                    "trust_banner": artifact.trust_banner,
                    "operator_id": artifact.operator_id,
                    "source_retention_verification_declared_sha256": artifact.source_retention_verification_declared_sha256,
                    "source_retention_verification_status": artifact.source_retention_verification_status,
                    "retention_verification_artifact_hash_valid": artifact.retention_verification_artifact_hash_valid,
                    "source_retention_receipt_status": artifact.source_retention_receipt_status,
                    "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
                    "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
                    "missing_entry_count": artifact.missing_entry_count,
                    "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
                    "signoff_statement_sha256": artifact.signoff_statement_sha256,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.signoff_status in {"SIGNED_OFF", "SIGNED_OFF_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-signoff":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_retention_signoff = str(getattr(ns, "retention_signoff_artifact", "") or "").strip()
        if raw_retention_signoff == ".":
            raw_retention_signoff = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_signoff_verification_artifact(
            retention_signoff_artifact_path=Path(raw_retention_signoff) if raw_retention_signoff else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.verification_status == "PASS",
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "verification_status": artifact.verification_status,
                    "trust_banner": artifact.trust_banner,
                    "source_retention_signoff_declared_sha256": artifact.source_retention_signoff_declared_sha256,
                    "source_retention_signoff_computed_sha256": artifact.source_retention_signoff_computed_sha256,
                    "source_retention_signoff_status": artifact.source_retention_signoff_status,
                    "retention_signoff_artifact_hash_valid": artifact.retention_signoff_artifact_hash_valid,
                    "signoff_statement_hash_valid": artifact.signoff_statement_hash_valid,
                    "source_retention_verification_declared_sha256": artifact.source_retention_verification_declared_sha256,
                    "source_retention_verification_status": artifact.source_retention_verification_status,
                    "retention_verification_artifact_hash_valid": artifact.retention_verification_artifact_hash_valid,
                    "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
                    "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
                    "missing_entry_count": artifact.missing_entry_count,
                    "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.verification_status == "PASS" else 2
    return None
