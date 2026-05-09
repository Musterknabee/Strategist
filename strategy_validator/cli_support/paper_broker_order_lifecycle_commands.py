"""Paper broker order lifecycle commands for the paper broker CLI.

This phase module keeps command bodies small while resolving runtime
dependencies through ``strategy_validator.cli.paper_broker`` so the
legacy monkeypatch surface remains stable.
"""
from __future__ import annotations

from typing import Any


_COMMANDS = frozenset(('select-intent', 'dry-run-order', 'dry-run-selected-intent', 'submit-paper-order', 'refresh-order-status',))


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

    if ns.cmd == "select-intent":
        intent = PaperBrokerOrderIntent(
            tracking_id=ns.tracking_id,
            symbol=ns.symbol,
            side=ns.side,
            qty=float(ns.qty),
        )
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        latest_path, history_path, artifact = write_paper_execution_intent_selection_artifact(
            intent,
            strategy_id=str(getattr(ns, "strategy_id", "") or "").strip() or None,
            selected_by=str(getattr(ns, "selected_by", "") or "operator"),
            selection_reason=str(getattr(ns, "reason", "") or "manual paper dry-run preparation"),
            source_artifact_path=str(getattr(ns, "source_artifact", "") or "").strip() or None,
            output_root=Path(raw_out_root) if raw_out_root else None,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": True,
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "dry_run_command_hint": artifact.dry_run_command_hint,
                    "selected_intent": artifact.selected_intent.model_dump(mode="json"),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0
    if ns.cmd == "dry-run-order":
        intent = PaperBrokerOrderIntent(
            tracking_id=ns.tracking_id,
            symbol=ns.symbol,
            side=ns.side,
            qty=float(ns.qty),
        )
        res = dry_run_paper_order(intent, env)
        payload = {"ok": res.ok, "result": res.model_dump(mode="json")}
        if not bool(getattr(ns, "no_artifact", False)):
            raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
            latest_path, history_path, artifact = write_paper_order_dry_run_artifact(
                intent,
                res,
                output_root=Path(raw_out_root) if raw_out_root else None,
            )
            payload.update(
                {
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                }
            )
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if ns.cmd == "dry-run-selected-intent":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_selection = str(getattr(ns, "selection_artifact", "") or "").strip()
        if raw_selection == ".":
            raw_selection = ""
        selection_path, selection = read_paper_execution_intent_selection_artifact(
            tracking_id=str(getattr(ns, "tracking_id", "") or "").strip() or None,
            selection_artifact_path=Path(raw_selection) if raw_selection else None,
            output_root=output_root,
        )
        if selection is None:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "blocked": ["SELECTED_INTENT_ARTIFACT_NOT_FOUND"],
                        "selection_artifact": str(selection_path) if selection_path is not None else None,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 2
        try:
            intent = PaperBrokerOrderIntent.model_validate(selection.get("broker_intent"))
        except ValueError as exc:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "blocked": ["SELECTED_INTENT_BROKER_INTENT_INVALID"],
                        "error": str(exc),
                        "selection_artifact": str(selection_path),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 2
        selection_sha = str(selection.get("artifact_sha256") or "").strip() or None
        res = dry_run_paper_order(intent, env)
        latest_path, history_path, artifact = write_paper_order_dry_run_artifact(
            intent,
            res,
            output_root=output_root,
            source_selection_artifact_path=str(selection_path) if selection_path is not None else None,
            source_selection_artifact_sha256=selection_sha,
        )
        payload = {
            "ok": res.ok,
            "replayed_from_selected_intent": True,
            "selection_artifact": str(selection_path) if selection_path is not None else None,
            "selected_intent_sha256": selection_sha,
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "dry_run_source_selection_sha256": artifact.source_selection_artifact_sha256,
            "intent": intent.model_dump(mode="json"),
            "result": res.model_dump(mode="json"),
        }
        sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        return 0
    if ns.cmd == "submit-paper-order":
        intent = PaperBrokerOrderIntent(
            tracking_id=ns.tracking_id,
            symbol=ns.symbol,
            side=ns.side,
            qty=float(ns.qty),
        )
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        guard = build_paper_submission_guard_snapshot(intent=intent, env=env, output_root=output_root)
        if guard.status != "PASS":
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "blocked": guard.blockers,
                        "submission_guard": guard.model_dump(mode="json"),
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 2
        res = submit_paper_order(intent, env)
        latest_path, history_path, artifact = write_paper_order_submission_artifact(
            intent=intent,
            result=res,
            guard_snapshot=guard,
            output_root=output_root,
        )
        redacted = res.model_dump(mode="json")
        sys.stdout.write(
            json.dumps(
                {
                    "ok": res.ok,
                    "result": redacted,
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "submission_guard": guard.model_dump(mode="json"),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if res.ok else 3
    if ns.cmd == "refresh-order-status":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_submission = str(getattr(ns, "submission_artifact", "") or "").strip()
        if raw_submission == ".":
            raw_submission = ""
        submission_path, submission_raw, submission_sha = find_latest_submission_artifact(
            tracking_id=str(getattr(ns, "tracking_id", "") or "").strip() or None,
            submission_artifact_path=Path(raw_submission) if raw_submission else None,
            output_root=output_root,
        )
        tracking_id = str(getattr(ns, "tracking_id", "") or "").strip() or tracking_id_from_submission(submission_path, submission_raw)
        broker_order_id = str(getattr(ns, "broker_order_id", "") or "").strip() or broker_order_id_from_submission(submission_raw)
        if not tracking_id or not broker_order_id:
            sys.stdout.write(
                json.dumps(
                    {
                        "ok": False,
                        "blocked": ["SUBMISSION_ARTIFACT_OR_BROKER_ORDER_ID_MISSING"],
                        "submission_artifact": str(submission_path) if submission_path is not None else None,
                        "tracking_id": tracking_id,
                        "broker_order_id": broker_order_id,
                    },
                    indent=2,
                    sort_keys=True,
                )
                + "\n"
            )
            return 2
        result = get_alpaca_paper_order_status(
            env,
            broker_order_id,
            allow_network=bool(getattr(ns, "allow_network", False)),
        )
        latest_path, history_path, artifact = write_paper_order_status_artifact(
            tracking_id=tracking_id,
            broker_order_id=broker_order_id,
            result=result,
            source_submission_artifact_path=str(submission_path) if submission_path is not None else None,
            source_submission_artifact_sha256=submission_sha,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": result.ok,
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "broker_order_id": broker_order_id,
                    "status": result.status,
                    "filled_qty": result.filled_qty,
                    "source_submission_artifact_sha256": submission_sha,
                    "result": result.model_dump(mode="json"),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if result.ok else 3
    return None
