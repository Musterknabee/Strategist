"""Custody archive, return, redeposit, and certification command handlers.

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

    if ns.cmd == "archive-evidence-bundle-retention-custody-closeout":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_closeout_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_archive_artifact(
            retention_custody_closeout_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            archived_by=str(getattr(ns, "archived_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            archive_note=str(getattr(ns, "archive_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.archive_status in {"ARCHIVED", "ARCHIVED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "archive_status": artifact.archive_status,
            "trust_banner": artifact.trust_banner,
            "custody_archive_id": artifact.custody_archive_id,
            "custody_closeout_id": artifact.custody_closeout_id,
            "custody_completion_id": artifact.custody_completion_id,
            "source_retention_custody_closeout_verification_status": artifact.source_retention_custody_closeout_verification_status,
            "custody_archive_statement_sha256": artifact.custody_archive_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.archive_status in {"ARCHIVED", "ARCHIVED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-archive":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_archive_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact(
            retention_custody_archive_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_archive_status": artifact.source_retention_custody_archive_status,
            "retention_custody_archive_artifact_hash_valid": artifact.retention_custody_archive_artifact_hash_valid,
            "custody_archive_statement_hash_valid": artifact.custody_archive_statement_hash_valid,
            "custody_archive_id": artifact.custody_archive_id,
            "custody_closeout_id": artifact.custody_closeout_id,
            "custody_completion_id": artifact.custody_completion_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "retrieve-evidence-bundle-retention-custody-archive":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_archive_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact(
            retention_custody_archive_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            retrieved_by=str(getattr(ns, "retrieved_by", "operator") or "operator"),
            retrieval_purpose=str(getattr(ns, "retrieval_purpose", "operator review") or "operator review"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            retrieval_note=str(getattr(ns, "retrieval_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.retrieval_status in {"RETRIEVED", "RETRIEVED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "retrieval_status": artifact.retrieval_status,
            "trust_banner": artifact.trust_banner,
            "custody_retrieval_id": artifact.custody_retrieval_id,
            "custody_archive_id": artifact.custody_archive_id,
            "custody_closeout_id": artifact.custody_closeout_id,
            "source_retention_custody_archive_verification_status": artifact.source_retention_custody_archive_verification_status,
            "custody_retrieval_statement_sha256": artifact.custody_retrieval_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.retrieval_status in {"RETRIEVED", "RETRIEVED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-retrieval":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_retrieval_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact(
            retention_custody_retrieval_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_retrieval_status": artifact.source_retention_custody_retrieval_status,
            "retention_custody_retrieval_artifact_hash_valid": artifact.retention_custody_retrieval_artifact_hash_valid,
            "custody_retrieval_statement_hash_valid": artifact.custody_retrieval_statement_hash_valid,
            "custody_retrieval_id": artifact.custody_retrieval_id,
            "custody_archive_id": artifact.custody_archive_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "return-evidence-bundle-retention-custody-retrieval":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_retrieval_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_return_artifact(
            retention_custody_retrieval_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            returned_by=str(getattr(ns, "returned_by", "operator") or "operator"),
            return_reason=str(getattr(ns, "return_reason", "retrieval complete") or "retrieval complete"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            return_note=str(getattr(ns, "return_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.return_status in {"RETURNED", "RETURNED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "return_status": artifact.return_status,
            "trust_banner": artifact.trust_banner,
            "custody_return_id": artifact.custody_return_id,
            "returned_by": artifact.returned_by,
            "return_reason": artifact.return_reason,
            "custody_return_statement_sha256": artifact.custody_return_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.return_status in {"RETURNED", "RETURNED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-return":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_return_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact(
            retention_custody_return_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_return_status": artifact.source_retention_custody_return_status,
            "retention_custody_return_artifact_hash_valid": artifact.retention_custody_return_artifact_hash_valid,
            "custody_return_statement_hash_valid": artifact.custody_return_statement_hash_valid,
            "custody_return_id": artifact.custody_return_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "redeposit-evidence-bundle-retention-custody-return":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_return_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact(
            retention_custody_return_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            redeposited_by=str(getattr(ns, "redeposited_by", "operator") or "operator"),
            redeposit_reason=str(getattr(ns, "redeposit_reason", "return verified") or "return verified"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            redeposit_note=str(getattr(ns, "redeposit_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.redeposit_status in {"REDEPOSITED", "REDEPOSITED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "redeposit_status": artifact.redeposit_status,
            "trust_banner": artifact.trust_banner,
            "custody_redeposit_id": artifact.custody_redeposit_id,
            "redeposited_by": artifact.redeposited_by,
            "redeposit_reason": artifact.redeposit_reason,
            "custody_redeposit_statement_sha256": artifact.custody_redeposit_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.redeposit_status in {"REDEPOSITED", "REDEPOSITED_RESTRICTED"} else 2


    if ns.cmd == "inventory-evidence-bundle-retention-custody-redeposit":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_redeposit_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_inventory_artifact(
            retention_custody_redeposit_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            inventoried_by=str(getattr(ns, "inventoried_by", "operator") or "operator"),
            inventory_reason=str(getattr(ns, "inventory_reason", "redeposit verified") or "redeposit verified"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            inventory_note=str(getattr(ns, "inventory_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.inventory_status in {"INVENTORIED", "INVENTORIED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "inventory_status": artifact.inventory_status,
            "trust_banner": artifact.trust_banner,
            "custody_inventory_id": artifact.custody_inventory_id,
            "inventoried_by": artifact.inventoried_by,
            "inventory_reason": artifact.inventory_reason,
            "custody_inventory_statement_sha256": artifact.custody_inventory_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.inventory_status in {"INVENTORIED", "INVENTORIED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-inventory":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_inventory_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact(
            retention_custody_inventory_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_inventory_status": artifact.source_retention_custody_inventory_status,
            "retention_custody_inventory_artifact_hash_valid": artifact.retention_custody_inventory_artifact_hash_valid,
            "custody_inventory_statement_hash_valid": artifact.custody_inventory_statement_hash_valid,
            "custody_inventory_id": artifact.custody_inventory_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "reconcile-evidence-bundle-retention-custody-inventory":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_inventory_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact(
            retention_custody_inventory_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            reconciled_by=str(getattr(ns, "reconciled_by", "operator") or "operator"),
            reconciliation_reason=str(getattr(ns, "reconciliation_reason", "inventory verification accepted") or "inventory verification accepted"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            reconciliation_note=str(getattr(ns, "reconciliation_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.reconciliation_status in {"RECONCILED", "RECONCILED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "reconciliation_status": artifact.reconciliation_status,
            "trust_banner": artifact.trust_banner,
            "custody_reconciliation_id": artifact.custody_reconciliation_id,
            "reconciled_by": artifact.reconciled_by,
            "reconciliation_reason": artifact.reconciliation_reason,
            "custody_reconciliation_statement_sha256": artifact.custody_reconciliation_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.reconciliation_status in {"RECONCILED", "RECONCILED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-reconciliation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_reconciliation_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact(
            retention_custody_reconciliation_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_reconciliation_status": artifact.source_retention_custody_reconciliation_status,
            "retention_custody_reconciliation_artifact_hash_valid": artifact.retention_custody_reconciliation_artifact_hash_valid,
            "custody_reconciliation_statement_hash_valid": artifact.custody_reconciliation_statement_hash_valid,
            "custody_reconciliation_id": artifact.custody_reconciliation_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "certify-evidence-bundle-retention-custody-reconciliation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_reconciliation_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_certification_artifact(
            retention_custody_reconciliation_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            certified_by=str(getattr(ns, "certified_by", "operator") or "operator"),
            certification_reason=str(getattr(ns, "certification_reason", "reconciliation verification accepted") or "reconciliation verification accepted"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            certification_note=str(getattr(ns, "certification_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.certification_status in {"CERTIFIED", "CERTIFIED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "certification_status": artifact.certification_status,
            "trust_banner": artifact.trust_banner,
            "custody_certification_id": artifact.custody_certification_id,
            "custody_reconciliation_id": artifact.custody_reconciliation_id,
            "certified_by": artifact.certified_by,
            "certification_reason": artifact.certification_reason,
            "custody_certification_statement_sha256": artifact.custody_certification_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.certification_status in {"CERTIFIED", "CERTIFIED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-certification":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_certification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact(
            retention_custody_certification_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_certification_status": artifact.source_retention_custody_certification_status,
            "retention_custody_certification_artifact_hash_valid": artifact.retention_custody_certification_artifact_hash_valid,
            "custody_certification_statement_hash_valid": artifact.custody_certification_statement_hash_valid,
            "custody_certification_id": artifact.custody_certification_id,
            "custody_reconciliation_id": artifact.custody_reconciliation_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "attest-evidence-bundle-retention-custody-certification":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_certification_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_attestation_artifact(
            retention_custody_certification_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            attested_by=str(getattr(ns, "attested_by", "operator") or "operator"),
            attestation_reason=str(getattr(ns, "attestation_reason", "certification verification accepted") or "certification verification accepted"),
            attestation_scope=str(getattr(ns, "attestation_scope", "paper-execution-retention-custody") or "paper-execution-retention-custody"),
            attestation_note=str(getattr(ns, "attestation_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "attestation_status": artifact.attestation_status,
            "trust_banner": artifact.trust_banner,
            "custody_attestation_id": artifact.custody_attestation_id,
            "custody_certification_id": artifact.custody_certification_id,
            "attested_by": artifact.attested_by,
            "attestation_reason": artifact.attestation_reason,
            "custody_attestation_statement_sha256": artifact.custody_attestation_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-attestation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_attestation_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact(
            retention_custody_attestation_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_attestation_status": artifact.source_retention_custody_attestation_status,
            "retention_custody_attestation_artifact_hash_valid": artifact.retention_custody_attestation_artifact_hash_valid,
            "custody_attestation_statement_hash_valid": artifact.custody_attestation_statement_hash_valid,
            "custody_attestation_id": artifact.custody_attestation_id,
            "custody_certification_id": artifact.custody_certification_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-redeposit":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_redeposit_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact(
            retention_custody_redeposit_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_redeposit_status": artifact.source_retention_custody_redeposit_status,
            "retention_custody_redeposit_artifact_hash_valid": artifact.retention_custody_redeposit_artifact_hash_valid,
            "custody_redeposit_statement_hash_valid": artifact.custody_redeposit_statement_hash_valid,
            "custody_redeposit_id": artifact.custody_redeposit_id,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    return None

