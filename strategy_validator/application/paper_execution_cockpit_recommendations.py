"""Recommended action synthesis for the paper execution cockpit read model."""
from __future__ import annotations

from typing import Any

def _recommended_actions(
    *,
    broker_policy: str,
    tracking_present: bool,
    intent_count: int,
    selected_count: int,
    blocked_count: int,
    journal_count: int,
    replay_status: str,
    freshness_gate: PaperExecutionFreshnessGate | None = None,
    submission_receipt_count: int = 0,
    submission_guard_blocker_count: int = 0,
    latest_submission_guard_status: str | None = None,
    position_reconciliation: PaperExecutionPositionReconciliationView | None = None,
    order_statuses: list[PaperExecutionOrderStatusView] | None = None,
    timeline_summary: PaperExecutionTimelineSummary | None = None,
    latest_evidence_bundle: Any | None = None,
    latest_evidence_bundle_verification: Any | None = None,
    latest_evidence_bundle_drift: Any | None = None,
    latest_evidence_bundle_rotation: Any | None = None,
    latest_evidence_bundle_rotation_execution: Any | None = None,
    latest_evidence_bundle_attestation: Any | None = None,
    latest_evidence_bundle_attestation_verification: Any | None = None,
    latest_evidence_bundle_closure: Any | None = None,
    latest_evidence_bundle_closure_verification: Any | None = None,
    latest_evidence_bundle_export_manifest: Any | None = None,
    latest_evidence_bundle_export_verification: Any | None = None,
    latest_evidence_bundle_retention_receipt: Any | None = None,
    latest_evidence_bundle_retention_verification: Any | None = None,
    latest_evidence_bundle_retention_signoff: Any | None = None,
    latest_evidence_bundle_retention_signoff_verification: Any | None = None,
    latest_evidence_bundle_retention_handoff: Any | None = None,
    latest_evidence_bundle_retention_handoff_verification: Any | None = None,
    latest_evidence_bundle_retention_handoff_acceptance: Any | None = None,
    latest_evidence_bundle_retention_handoff_acceptance_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_register: Any | None = None,
    latest_evidence_bundle_retention_custody_register_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_seal: Any | None = None,
    latest_evidence_bundle_retention_custody_seal_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_audit: Any | None = None,
    latest_evidence_bundle_retention_custody_audit_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_continuity: Any | None = None,
    latest_evidence_bundle_retention_custody_continuity_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_review: Any | None = None,
    latest_evidence_bundle_retention_custody_review_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_renewal: Any | None = None,
    latest_evidence_bundle_retention_custody_renewal_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_schedule: Any | None = None,
    latest_evidence_bundle_retention_custody_schedule_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_notice: Any | None = None,
    latest_evidence_bundle_retention_custody_notice_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_acknowledgment: Any | None = None,
    latest_evidence_bundle_retention_custody_acknowledgment_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_completion: Any | None = None,
    latest_evidence_bundle_retention_custody_completion_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_closeout: Any | None = None,
    latest_evidence_bundle_retention_custody_closeout_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_archive: Any | None = None,
    latest_evidence_bundle_retention_custody_archive_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_retrieval: Any | None = None,
    latest_evidence_bundle_retention_custody_retrieval_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_return: Any | None = None,
    latest_evidence_bundle_retention_custody_return_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_redeposit: Any | None = None,
    latest_evidence_bundle_retention_custody_redeposit_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_inventory: Any | None = None,
    latest_evidence_bundle_retention_custody_inventory_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_reconciliation: Any | None = None,
    latest_evidence_bundle_retention_custody_reconciliation_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_certification: Any | None = None,
    latest_evidence_bundle_retention_custody_certification_verification: Any | None = None,
    latest_evidence_bundle_retention_custody_attestation: Any | None = None,
    latest_evidence_bundle_retention_custody_attestation_verification: Any | None = None,
) -> list[str]:
    actions: list[str] = []
    if broker_policy != "PAPER_READY":
        actions.append("Resolve paper broker policy blockers or missing Alpaca paper keys before CLI dry-run/order evidence.")
    if not tracking_present:
        actions.append("Enroll at least one strategy into paper tracking before generating paper execution previews.")
    if tracking_present and intent_count == 0:
        actions.append("Append a daily paper signal snapshot so the cockpit can derive a candidate execution intent.")
    if tracking_present and selected_count == 0:
        actions.append("Select a paper execution intent with strategy-validator-paper-broker select-intent before durable dry-run evidence.")
    if selected_count and replay_status == "NO_DRY_RUN":
        actions.append("Replay the selected intent with strategy-validator-paper-broker dry-run-selected-intent to bind dry-run evidence to the selection SHA.")
    if replay_status == "MISMATCHED":
        actions.append("Latest linked dry-run evidence does not match the current selected intent SHA; rerun dry-run-selected-intent.")
    if freshness_gate is not None:
        if freshness_gate.status == "STALE":
            actions.append("Refresh stale paper execution evidence: reselect the intent if needed, rerun dry-run-selected-intent, and regenerate broker policy/status evidence.")
        elif freshness_gate.status == "REPLAY_REQUIRED":
            actions.append("Freshness gate requires replay: run strategy-validator-paper-broker dry-run-selected-intent for the current selected intent.")
        elif freshness_gate.status == "MISSING_EVIDENCE":
            actions.append("Freshness gate is missing required paper execution evidence; select an intent and materialize linked dry-run evidence before trusting the cockpit.")
    if blocked_count:
        actions.append("Inspect dry-run blockers; browser routes intentionally cannot bypass broker policy.")
    if submission_receipt_count and submission_guard_blocker_count:
        actions.append("Review guarded paper submission receipt blockers before trusting the latest paper submission artifact.")
    if latest_submission_guard_status == "PASS":
        actions.append("Latest paper submission receipt is guard-passed; keep reviewing CLI-only receipts before any operational decision.")
    if latest_submission_guard_status == "PASS" and not order_statuses:
        actions.append("Refresh broker order status with strategy-validator-paper-broker refresh-order-status after guarded paper submission.")
    if order_statuses and order_statuses[0].status not in {"filled", "partially_filled"}:
        actions.append("Latest paper order status is not filled; refresh order status before expecting position reconciliation.")
    if timeline_summary is not None:
        if timeline_summary.sequence_status == "PARTIAL":
            actions.append("Review the paper execution timeline and complete missing evidence stages before trusting the paper execution loop.")
        elif timeline_summary.sequence_status == "BLOCKED":
            actions.append("Resolve paper execution timeline blockers before treating CLI evidence as trusted.")
        elif timeline_summary.sequence_status == "COMPLETE" and latest_evidence_bundle is None:
            actions.append("Seal the completed paper execution timeline with strategy-validator-paper-broker seal-evidence-bundle for digest-anchored review evidence.")
    if latest_evidence_bundle is not None:
        if getattr(latest_evidence_bundle, "trust_banner", "TRUST_RESTRICTED") != "TRUSTED":
            actions.append("Review the latest paper execution evidence bundle warnings/blockers before treating the timeline as trusted.")
        if latest_evidence_bundle_verification is None:
            actions.append("Verify the sealed paper execution evidence bundle with strategy-validator-paper-broker verify-evidence-bundle before treating it as independently trusted.")
    if latest_evidence_bundle_verification is not None:
        if getattr(latest_evidence_bundle_verification, "verification_status", "FAIL") != "PASS":
            actions.append("Latest paper execution evidence bundle verification failed; re-seal or repair mismatched source artifacts before relying on the bundle.")
    if latest_evidence_bundle is not None and latest_evidence_bundle_drift is None:
        actions.append("Check sealed-bundle drift with strategy-validator-paper-broker check-evidence-bundle-drift after verifying the bundle.")
    if latest_evidence_bundle_drift is not None:
        if getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") == "DRIFTED":
            actions.append("Latest verified paper execution bundle is drifted from the current timeline; re-seal and re-verify the evidence bundle.")
        elif getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") in {"NO_BUNDLE", "NO_TIMELINE"}:
            actions.append("Bundle drift check cannot establish current trust; complete the timeline and seal a bundle before relying on paper execution evidence.")
    if latest_evidence_bundle_rotation is not None:
        rotation_status = getattr(latest_evidence_bundle_rotation, "rotation_status", "UNKNOWN")
        if rotation_status == "REQUIRED":
            actions.append("Run strategy-validator-paper-broker run-evidence-bundle-rotation to execute the safe re-seal / verify / drift-check workflow.")
        elif rotation_status == "RECOMMENDED":
            actions.append("Run strategy-validator-paper-broker run-evidence-bundle-rotation to follow the latest paper evidence-bundle rotation recommendation.")
        elif rotation_status == "BLOCKED":
            actions.append("Resolve paper evidence-bundle rotation blockers before resealing the timeline.")
    if latest_evidence_bundle_rotation_execution is not None:
        execution_status = getattr(latest_evidence_bundle_rotation_execution, "rotation_execution_status", "UNKNOWN")
        if execution_status == "FAILED":
            actions.append("Latest paper evidence-bundle rotation execution failed; inspect the execution manifest and repair failed steps before trusting the bundle.")
        elif execution_status == "BLOCKED":
            actions.append("Latest paper evidence-bundle rotation execution is blocked; complete timeline or recommendation prerequisites before rerunning.")
        elif execution_status == "SKIPPED":
            actions.append("Latest paper evidence-bundle rotation execution was skipped because rotation was not needed; continue drift monitoring.")
    if latest_evidence_bundle_attestation is None:
        if latest_evidence_bundle_verification is not None and getattr(latest_evidence_bundle_verification, "verification_status", "UNKNOWN") == "PASS" and latest_evidence_bundle_drift is not None and getattr(latest_evidence_bundle_drift, "drift_status", "UNKNOWN") == "IN_SYNC":
            actions.append("Write a keyless local paper evidence-bundle attestation with strategy-validator-paper-broker attest-evidence-bundle.")
    else:
        attestation_status = getattr(latest_evidence_bundle_attestation, "attestation_status", "UNKNOWN")
        if attestation_status == "BLOCKED":
            actions.append("Paper evidence-bundle attestation is blocked; verify bundle and resolve drift before attesting.")
        elif getattr(latest_evidence_bundle_attestation, "blocker_count", 0):
            actions.append("Review paper evidence-bundle attestation blockers before trusting attested paper execution evidence.")
        if latest_evidence_bundle_attestation_verification is None and attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"}:
            actions.append("Verify the paper evidence-bundle attestation with strategy-validator-paper-broker verify-evidence-bundle-attestation before treating the attestation artifact as tamper-checked.")
    if latest_evidence_bundle_attestation_verification is not None:
        attestation_verification_status = getattr(latest_evidence_bundle_attestation_verification, "verification_status", "UNKNOWN")
        if attestation_verification_status != "PASS":
            actions.append("Latest paper evidence-bundle attestation verification failed; inspect attestation hash, payload, and referenced artifact links before relying on it.")
        elif latest_evidence_bundle_closure is None:
            actions.append("Write a final paper evidence-bundle closure packet with strategy-validator-paper-broker close-evidence-bundle.")
    if latest_evidence_bundle_closure is not None:
        closure_status = getattr(latest_evidence_bundle_closure, "closure_status", "UNKNOWN")
        if closure_status == "BLOCKED":
            actions.append("Paper evidence-bundle closure is blocked; resolve closure blockers before relying on the paper evidence chain.")
        elif closure_status == "READY_RESTRICTED":
            actions.append("Paper evidence-bundle closure is restricted; review closure warnings before archiving the paper evidence chain.")
        elif latest_evidence_bundle_closure_verification is None:
            actions.append("Verify the paper evidence-bundle closure packet with strategy-validator-paper-broker verify-evidence-bundle-closure before archiving the evidence chain.")
    if latest_evidence_bundle_closure_verification is not None:
        closure_verification_status = getattr(latest_evidence_bundle_closure_verification, "verification_status", "UNKNOWN")
        if closure_verification_status != "PASS":
            actions.append("Latest paper evidence-bundle closure verification failed; inspect closure hash and referenced artifact links before archiving the chain.")
        elif latest_evidence_bundle_export_manifest is None:
            actions.append("Write a paper evidence-chain export handoff manifest with strategy-validator-paper-broker export-evidence-bundle-chain before external retention.")
    if latest_evidence_bundle_export_manifest is not None:
        export_status = getattr(latest_evidence_bundle_export_manifest, "export_status", "UNKNOWN")
        if export_status == "BLOCKED":
            actions.append("Paper evidence-chain export handoff manifest is blocked; repair missing or mismatched retained artifacts before external retention.")
        elif export_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain export handoff manifest is restricted; review warnings before external retention.")
        elif latest_evidence_bundle_export_verification is None:
            actions.append("Verify the paper evidence-chain export handoff manifest with strategy-validator-paper-broker verify-evidence-bundle-export before external retention.")
    if latest_evidence_bundle_export_verification is not None:
        export_verification_status = getattr(latest_evidence_bundle_export_verification, "verification_status", "UNKNOWN")
        if export_verification_status != "PASS":
            actions.append("Latest paper evidence-chain export verification failed; inspect export manifest hash, index hash, and retained artifact entry digests before external retention.")
        elif latest_evidence_bundle_retention_receipt is None:
            actions.append("Write a paper evidence-chain retention receipt with strategy-validator-paper-broker receipt-evidence-bundle-retention before external retention.")
    if latest_evidence_bundle_retention_receipt is not None:
        retention_status = getattr(latest_evidence_bundle_retention_receipt, "retention_status", "UNKNOWN")
        if retention_status == "BLOCKED":
            actions.append("Paper evidence-chain retention receipt is blocked; inspect missing or mismatched retained files before external retention.")
        elif retention_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain retention receipt is restricted; review warnings before external retention.")
        elif latest_evidence_bundle_retention_verification is None:
            actions.append("Verify the paper evidence-chain retention receipt with strategy-validator-paper-broker verify-evidence-bundle-retention before external retention.")
    if latest_evidence_bundle_retention_verification is not None:
        retention_verification_status = getattr(latest_evidence_bundle_retention_verification, "verification_status", "UNKNOWN")
        if retention_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention verification failed; inspect retention receipt hash, index hash, file digests, and sizes before external retention.")
        elif latest_evidence_bundle_retention_signoff is None:
            actions.append("Write a paper evidence-chain retention signoff with strategy-validator-paper-broker signoff-evidence-bundle-retention before external retention handoff.")
    if latest_evidence_bundle_retention_signoff is not None:
        signoff_status = getattr(latest_evidence_bundle_retention_signoff, "signoff_status", "UNKNOWN")
        if signoff_status == "BLOCKED":
            actions.append("Paper evidence-chain retention signoff is blocked; inspect signoff blockers before external retention handoff.")
        elif signoff_status == "SIGNED_OFF_RESTRICTED":
            actions.append("Paper evidence-chain retention signoff is restricted; review warnings before external retention handoff.")
        elif latest_evidence_bundle_retention_signoff_verification is None:
            actions.append("Verify the paper evidence-chain retention signoff with strategy-validator-paper-broker verify-evidence-bundle-retention-signoff before external retention handoff.")
    if latest_evidence_bundle_retention_signoff_verification is not None:
        signoff_verification_status = getattr(latest_evidence_bundle_retention_signoff_verification, "verification_status", "UNKNOWN")
        if signoff_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention signoff verification failed; inspect signoff artifact hash, statement hash, and source retention verification digest before external retention handoff.")
        elif latest_evidence_bundle_retention_handoff is None:
            actions.append("Write a final paper evidence-chain retention handoff capsule with strategy-validator-paper-broker handoff-evidence-bundle-retention before custody acceptance.")
    if latest_evidence_bundle_retention_handoff is not None:
        handoff_status = getattr(latest_evidence_bundle_retention_handoff, "handoff_status", "UNKNOWN")
        if handoff_status == "BLOCKED":
            actions.append("Paper evidence-chain retention handoff is blocked; inspect handoff blockers before custody acceptance.")
        elif handoff_status == "READY_RESTRICTED":
            actions.append("Paper evidence-chain retention handoff is restricted; review warnings before custody acceptance.")
        elif latest_evidence_bundle_retention_handoff_verification is None:
            actions.append("Verify the paper evidence-chain retention handoff with strategy-validator-paper-broker verify-evidence-bundle-retention-handoff before custody acceptance.")
    if latest_evidence_bundle_retention_handoff_verification is not None:
        handoff_verification_status = getattr(latest_evidence_bundle_retention_handoff_verification, "verification_status", "UNKNOWN")
        if handoff_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention handoff verification failed; inspect handoff artifact hash, statement hash, and source signoff verification digest before custody acceptance.")
        elif latest_evidence_bundle_retention_handoff_acceptance is None:
            actions.append("Accept the verified paper evidence-chain retention handoff with strategy-validator-paper-broker accept-evidence-bundle-retention-handoff before custody registration.")
    if latest_evidence_bundle_retention_handoff_acceptance is not None:
        acceptance_status = getattr(latest_evidence_bundle_retention_handoff_acceptance, "acceptance_status", "UNKNOWN")
        if acceptance_status == "BLOCKED":
            actions.append("Paper evidence-chain retention handoff acceptance is blocked; inspect acceptance blockers before custody registration.")
        elif acceptance_status == "ACCEPTED_RESTRICTED":
            actions.append("Paper evidence-chain retention handoff acceptance is restricted; review warnings before custody registration.")
        elif latest_evidence_bundle_retention_handoff_acceptance_verification is None:
            actions.append("Verify the paper evidence-chain retention handoff acceptance with strategy-validator-paper-broker verify-evidence-bundle-retention-handoff-acceptance before custody registration.")
    if latest_evidence_bundle_retention_handoff_acceptance_verification is not None:
        acceptance_verification_status = getattr(latest_evidence_bundle_retention_handoff_acceptance_verification, "verification_status", "UNKNOWN")
        if acceptance_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention handoff acceptance verification failed; inspect acceptance artifact hash, statement hash, and source handoff verification digest before custody registration.")
        elif latest_evidence_bundle_retention_custody_register is None:
            actions.append("Register the accepted paper evidence-chain retention custody with strategy-validator-paper-broker register-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_register is not None:
        register_status = getattr(latest_evidence_bundle_retention_custody_register, "register_status", "UNKNOWN")
        if register_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody register is blocked; inspect register blockers before final custody verification.")
        elif register_status == "REGISTERED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody register is restricted; review warnings before final custody verification.")
        elif latest_evidence_bundle_retention_custody_register_verification is None:
            actions.append("Verify the paper evidence-chain retention custody register with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-register.")
    if latest_evidence_bundle_retention_custody_register_verification is not None:
        custody_register_verification_status = getattr(latest_evidence_bundle_retention_custody_register_verification, "verification_status", "UNKNOWN")
        if custody_register_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody register verification failed; inspect register hash, statement hash, and source acceptance verification digest.")
        elif latest_evidence_bundle_retention_custody_seal is None:
            actions.append("Seal the verified paper evidence-chain retention custody with strategy-validator-paper-broker seal-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_seal is not None:
        seal_status = getattr(latest_evidence_bundle_retention_custody_seal, "seal_status", "UNKNOWN")
        if seal_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody seal is blocked; inspect seal blockers before final verification.")
        elif seal_status == "SEALED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody seal is restricted; review warnings before relying on the sealed custody state.")
        elif latest_evidence_bundle_retention_custody_seal_verification is None:
            actions.append("Verify the paper evidence-chain retention custody seal with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-seal.")
    if latest_evidence_bundle_retention_custody_seal_verification is not None:
        seal_verification_status = getattr(latest_evidence_bundle_retention_custody_seal_verification, "verification_status", "UNKNOWN")
        if seal_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody seal verification failed; inspect seal hash, statement hash, and source custody-register verification digest.")
        elif latest_evidence_bundle_retention_custody_audit is None:
            actions.append("Audit the verified paper evidence-chain retention custody seal with strategy-validator-paper-broker audit-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_audit is not None:
        audit_status = getattr(latest_evidence_bundle_retention_custody_audit, "audit_status", "UNKNOWN")
        if audit_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody audit is blocked; inspect audit blockers before relying on retained custody evidence.")
        elif audit_status == "AUDITED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody audit is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_audit_verification is None:
            actions.append("Verify the paper evidence-chain retention custody audit with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-audit.")
    if latest_evidence_bundle_retention_custody_audit_verification is not None:
        audit_verification_status = getattr(latest_evidence_bundle_retention_custody_audit_verification, "verification_status", "UNKNOWN")
        if audit_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody audit verification failed; inspect audit hash, statement hash, and source custody-seal verification digest.")
        elif latest_evidence_bundle_retention_custody_continuity is None:
            actions.append("Attest paper evidence-chain retention custody continuity with strategy-validator-paper-broker attest-evidence-bundle-retention-custody-continuity.")
    if latest_evidence_bundle_retention_custody_continuity is not None:
        continuity_status = getattr(latest_evidence_bundle_retention_custody_continuity, "continuity_status", "UNKNOWN")
        if continuity_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody continuity is blocked; inspect continuity blockers before verification.")
        elif continuity_status == "CONTINUITY_RESTRICTED":
            actions.append("Paper evidence-chain retention custody continuity is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_continuity_verification is None:
            actions.append("Verify the paper evidence-chain retention custody continuity attestation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-continuity.")
    if latest_evidence_bundle_retention_custody_continuity_verification is not None:
        continuity_verification_status = getattr(latest_evidence_bundle_retention_custody_continuity_verification, "verification_status", "UNKNOWN")
        if continuity_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody continuity verification failed; inspect continuity hash, statement hash, and source custody-audit verification digest.")
        elif latest_evidence_bundle_retention_custody_review is None:
            actions.append("Review the paper evidence-chain retention custody continuity with strategy-validator-paper-broker review-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_review is not None:
        review_status = getattr(latest_evidence_bundle_retention_custody_review, "review_status", "UNKNOWN")
        if review_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody review is blocked; inspect review blockers before verification.")
        elif review_status == "REVIEW_RESTRICTED":
            actions.append("Paper evidence-chain retention custody review is restricted; review warnings before relying on retained custody evidence.")
        elif latest_evidence_bundle_retention_custody_review_verification is None:
            actions.append("Verify the paper evidence-chain retention custody review with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-review.")
    if latest_evidence_bundle_retention_custody_review_verification is not None:
        review_verification_status = getattr(latest_evidence_bundle_retention_custody_review_verification, "verification_status", "UNKNOWN")
        if review_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody review verification failed; inspect review hash, statement hash, and source custody-continuity verification digest.")
        elif latest_evidence_bundle_retention_custody_renewal is None:
            actions.append("Renew the verified paper evidence-chain retention custody with strategy-validator-paper-broker renew-evidence-bundle-retention-custody.")
    if latest_evidence_bundle_retention_custody_renewal is not None:
        renewal_status = getattr(latest_evidence_bundle_retention_custody_renewal, "renewal_status", "UNKNOWN")
        if renewal_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal is blocked; inspect renewal blockers before scheduling the next renewal.")
        elif renewal_status == "RENEWAL_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal is restricted; review warnings before scheduling the next renewal.")
        elif latest_evidence_bundle_retention_custody_renewal_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_renewal_verification is not None:
        renewal_verification_status = getattr(latest_evidence_bundle_retention_custody_renewal_verification, "verification_status", "UNKNOWN")
        if renewal_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal verification failed; inspect renewal hash, statement hash, and source custody-review verification digest.")
        elif latest_evidence_bundle_retention_custody_schedule is None:
            actions.append("Schedule the next paper evidence-chain retention custody renewal with strategy-validator-paper-broker schedule-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_schedule is not None:
        schedule_status = getattr(latest_evidence_bundle_retention_custody_schedule, "schedule_status", "UNKNOWN")
        if schedule_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal schedule is blocked; inspect schedule blockers before relying on the due date.")
        elif schedule_status == "SCHEDULE_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal schedule is restricted; review warnings before relying on the due date.")
        elif latest_evidence_bundle_retention_custody_schedule_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal schedule with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-schedule.")
    if latest_evidence_bundle_retention_custody_schedule_verification is not None:
        schedule_verification_status = getattr(latest_evidence_bundle_retention_custody_schedule_verification, "verification_status", "UNKNOWN")
        if schedule_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal schedule verification failed; inspect schedule hash, statement hash, and source custody-renewal verification digest.")
        elif latest_evidence_bundle_retention_custody_notice is None:
            actions.append("Generate the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker notice-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_notice is not None:
        notice_status = getattr(latest_evidence_bundle_retention_custody_notice, "notice_status", "UNKNOWN")
        if notice_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal notice is blocked; inspect notice blockers before verification.")
        elif notice_status == "NOTICE_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal notice is restricted; inspect warnings before relying on renewal scheduling notice.")
        elif latest_evidence_bundle_retention_custody_notice_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-notice.")
    if latest_evidence_bundle_retention_custody_notice_verification is not None:
        notice_verification_status = getattr(latest_evidence_bundle_retention_custody_notice_verification, "verification_status", "UNKNOWN")
        if notice_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal notice verification failed; inspect notice hash, statement hash, and source schedule verification digest.")
        elif latest_evidence_bundle_retention_custody_acknowledgment is None:
            actions.append("Acknowledge the paper evidence-chain retention custody renewal notice with strategy-validator-paper-broker acknowledge-evidence-bundle-retention-custody-notice.")
    if latest_evidence_bundle_retention_custody_acknowledgment is not None:
        acknowledgment_status = getattr(latest_evidence_bundle_retention_custody_acknowledgment, "acknowledgment_status", "UNKNOWN")
        if acknowledgment_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal notice acknowledgment is blocked; inspect acknowledgment blockers before verification.")
        elif acknowledgment_status == "ACKNOWLEDGED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal notice acknowledgment is restricted; inspect warnings before treating the notice as operator-accepted.")
        elif latest_evidence_bundle_retention_custody_acknowledgment_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal notice acknowledgment with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-acknowledgment.")
    if latest_evidence_bundle_retention_custody_acknowledgment_verification is not None:
        acknowledgment_verification_status = getattr(latest_evidence_bundle_retention_custody_acknowledgment_verification, "verification_status", "UNKNOWN")
        if acknowledgment_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal notice acknowledgment verification failed; inspect acknowledgment hash, statement hash, and source notice verification digest.")
        elif latest_evidence_bundle_retention_custody_completion is None:
            actions.append("Complete the paper evidence-chain retention custody renewal with strategy-validator-paper-broker complete-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_completion is not None:
        completion_status = getattr(latest_evidence_bundle_retention_custody_completion, "completion_status", "UNKNOWN")
        if completion_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal completion is blocked; inspect completion blockers before verification.")
        elif completion_status == "COMPLETED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal completion is restricted; inspect warnings before closing out the renewal cycle.")
        elif latest_evidence_bundle_retention_custody_completion_verification is None:
            actions.append("Verify the paper evidence-chain retention custody renewal completion with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-completion.")
    if latest_evidence_bundle_retention_custody_completion_verification is not None:
        completion_verification_status = getattr(latest_evidence_bundle_retention_custody_completion_verification, "verification_status", "UNKNOWN")
        if completion_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody renewal completion verification failed; inspect completion hash, statement hash, and source acknowledgment verification digest.")
        elif latest_evidence_bundle_retention_custody_closeout is None:
            actions.append("Close out the verified paper evidence-chain retention custody renewal cycle with strategy-validator-paper-broker closeout-evidence-bundle-retention-custody-renewal.")
    if latest_evidence_bundle_retention_custody_closeout is not None:
        closeout_status = getattr(latest_evidence_bundle_retention_custody_closeout, "closeout_status", "UNKNOWN")
        if closeout_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody renewal closeout is blocked; inspect closeout blockers before verification.")
        elif closeout_status == "CLOSED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody renewal closeout is restricted; inspect warnings before treating the renewal cycle as closed.")
        elif latest_evidence_bundle_retention_custody_closeout_verification is None:
            actions.append("Verify the paper evidence-chain retention custody closeout with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-closeout.")
    if latest_evidence_bundle_retention_custody_closeout_verification is not None:
        closeout_verification_status = getattr(latest_evidence_bundle_retention_custody_closeout_verification, "verification_status", "UNKNOWN")
        if closeout_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody closeout verification failed; inspect closeout hash, statement hash, and source completion verification digest.")
        elif latest_evidence_bundle_retention_custody_archive is None:
            actions.append("Archive the verified paper evidence-chain retention custody closeout with strategy-validator-paper-broker archive-evidence-bundle-retention-custody-closeout.")
    if latest_evidence_bundle_retention_custody_archive is not None:
        archive_status = getattr(latest_evidence_bundle_retention_custody_archive, "archive_status", "UNKNOWN")
        if archive_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody archive is blocked; inspect archive blockers before verification.")
        elif archive_status == "ARCHIVED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody archive is restricted; inspect warnings before retrieval.")
        elif latest_evidence_bundle_retention_custody_archive_verification is None:
            actions.append("Verify the paper evidence-chain retention custody archive with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-archive.")
    if latest_evidence_bundle_retention_custody_archive_verification is not None:
        archive_verification_status = getattr(latest_evidence_bundle_retention_custody_archive_verification, "verification_status", "UNKNOWN")
        if archive_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody archive verification failed; inspect archive hash, statement hash, and source closeout verification digest.")
        elif latest_evidence_bundle_retention_custody_retrieval is None:
            actions.append("Retrieve the verified archived paper evidence-chain retention custody bundle with strategy-validator-paper-broker retrieve-evidence-bundle-retention-custody-archive.")
    if latest_evidence_bundle_retention_custody_retrieval is not None:
        retrieval_status = getattr(latest_evidence_bundle_retention_custody_retrieval, "retrieval_status", "UNKNOWN")
        if retrieval_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody retrieval is blocked; inspect retrieval blockers before verification.")
        elif retrieval_status == "RETRIEVED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody retrieval is restricted; inspect warnings before relying on retrieval evidence.")
        elif latest_evidence_bundle_retention_custody_retrieval_verification is None:
            actions.append("Verify the paper evidence-chain retention custody retrieval with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-retrieval.")
    if latest_evidence_bundle_retention_custody_retrieval_verification is not None:
        retrieval_verification_status = getattr(latest_evidence_bundle_retention_custody_retrieval_verification, "verification_status", "UNKNOWN")
        if retrieval_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody retrieval verification failed; inspect retrieval hash, statement hash, and source archive verification digest.")
        elif latest_evidence_bundle_retention_custody_return is None:
            actions.append("Return the verified retrieved paper evidence-chain retention custody bundle with strategy-validator-paper-broker return-evidence-bundle-retention-custody-retrieval.")
    if latest_evidence_bundle_retention_custody_return is not None:
        return_status = getattr(latest_evidence_bundle_retention_custody_return, "return_status", "UNKNOWN")
        if return_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody return is blocked; inspect return blockers before verification.")
        elif return_status == "RETURNED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody return is restricted; inspect warnings before relying on return evidence.")
        elif latest_evidence_bundle_retention_custody_return_verification is None:
            actions.append("Verify the paper evidence-chain retention custody return with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-return.")
    if latest_evidence_bundle_retention_custody_return_verification is not None:
        return_verification_status = getattr(latest_evidence_bundle_retention_custody_return_verification, "verification_status", "UNKNOWN")
        if return_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody return verification failed; inspect return hash, statement hash, and source retrieval verification digest.")
        elif latest_evidence_bundle_retention_custody_redeposit is None:
            actions.append("Redeposit the verified returned paper evidence-chain retention custody bundle with strategy-validator-paper-broker redeposit-evidence-bundle-retention-custody-return.")
    if latest_evidence_bundle_retention_custody_redeposit is not None:
        redeposit_status = getattr(latest_evidence_bundle_retention_custody_redeposit, "redeposit_status", "UNKNOWN")
        if redeposit_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody redeposit is blocked; inspect redeposit blockers before verification.")
        elif redeposit_status == "REDEPOSITED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody redeposit is restricted; inspect warnings before relying on redeposit evidence.")
        elif latest_evidence_bundle_retention_custody_redeposit_verification is None:
            actions.append("Verify the paper evidence-chain retention custody redeposit with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-redeposit.")
    if latest_evidence_bundle_retention_custody_redeposit_verification is not None:
        redeposit_verification_status = getattr(latest_evidence_bundle_retention_custody_redeposit_verification, "verification_status", "UNKNOWN")
        if redeposit_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody redeposit verification failed; inspect redeposit hash, statement hash, and source return verification digest.")
        elif latest_evidence_bundle_retention_custody_inventory is None:
            actions.append("Inventory the verified redeposited paper evidence-chain retention custody bundle with strategy-validator-paper-broker inventory-evidence-bundle-retention-custody-redeposit.")
    if latest_evidence_bundle_retention_custody_inventory is not None:
        inventory_status = getattr(latest_evidence_bundle_retention_custody_inventory, "inventory_status", "UNKNOWN")
        if inventory_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody inventory is blocked; inspect inventory blockers before verification.")
        elif inventory_status == "INVENTORIED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody inventory is restricted; inspect warnings before relying on inventory evidence.")
        elif latest_evidence_bundle_retention_custody_inventory_verification is None:
            actions.append("Verify the paper evidence-chain retention custody inventory with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-inventory.")
    if latest_evidence_bundle_retention_custody_inventory_verification is not None:
        inventory_verification_status = getattr(latest_evidence_bundle_retention_custody_inventory_verification, "verification_status", "UNKNOWN")
        if inventory_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody inventory verification failed; inspect inventory hash, statement hash, and source redeposit verification digest.")
        elif latest_evidence_bundle_retention_custody_reconciliation is None:
            actions.append("Reconcile the verified paper evidence-chain retention custody inventory with strategy-validator-paper-broker reconcile-evidence-bundle-retention-custody-inventory.")
    if latest_evidence_bundle_retention_custody_reconciliation is not None:
        reconciliation_status = getattr(latest_evidence_bundle_retention_custody_reconciliation, "reconciliation_status", "UNKNOWN")
        if reconciliation_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody reconciliation is blocked; inspect reconciliation blockers before verification.")
        elif reconciliation_status == "RECONCILED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody reconciliation is restricted; inspect warnings before relying on reconciliation evidence.")
        elif latest_evidence_bundle_retention_custody_reconciliation_verification is None:
            actions.append("Verify the paper evidence-chain retention custody reconciliation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-reconciliation.")
    if latest_evidence_bundle_retention_custody_reconciliation_verification is not None:
        reconciliation_verification_status = getattr(latest_evidence_bundle_retention_custody_reconciliation_verification, "verification_status", "UNKNOWN")
        if reconciliation_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody reconciliation verification failed; inspect reconciliation hash, statement hash, and source inventory verification digest.")
        elif latest_evidence_bundle_retention_custody_certification is None:
            actions.append("Certify the verified paper evidence-chain retention custody reconciliation with strategy-validator-paper-broker certify-evidence-bundle-retention-custody-reconciliation.")
    if latest_evidence_bundle_retention_custody_certification is not None:
        certification_status = getattr(latest_evidence_bundle_retention_custody_certification, "certification_status", "UNKNOWN")
        if certification_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody certification is blocked; inspect certification blockers before verification.")
        elif certification_status == "CERTIFIED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody certification is restricted; inspect warnings before relying on certification evidence.")
        elif latest_evidence_bundle_retention_custody_certification_verification is None:
            actions.append("Verify the paper evidence-chain retention custody certification with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-certification.")
    if latest_evidence_bundle_retention_custody_certification_verification is not None:
        certification_verification_status = getattr(latest_evidence_bundle_retention_custody_certification_verification, "verification_status", "UNKNOWN")
        if certification_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody certification verification failed; inspect certification hash, statement hash, and source reconciliation verification digest.")
        elif latest_evidence_bundle_retention_custody_attestation is None:
            actions.append("Attest the verified paper evidence-chain retention custody certification with strategy-validator-paper-broker attest-evidence-bundle-retention-custody-certification.")
    if latest_evidence_bundle_retention_custody_attestation is not None:
        attestation_status = getattr(latest_evidence_bundle_retention_custody_attestation, "attestation_status", "UNKNOWN")
        if attestation_status == "BLOCKED":
            actions.append("Paper evidence-chain retention custody attestation is blocked; inspect attestation blockers before verification.")
        elif attestation_status == "ATTESTED_RESTRICTED":
            actions.append("Paper evidence-chain retention custody attestation is restricted; inspect warnings before relying on attestation evidence.")
        elif latest_evidence_bundle_retention_custody_attestation_verification is None:
            actions.append("Verify the paper evidence-chain retention custody attestation with strategy-validator-paper-broker verify-evidence-bundle-retention-custody-attestation.")
    if latest_evidence_bundle_retention_custody_attestation_verification is not None:
        attestation_verification_status = getattr(latest_evidence_bundle_retention_custody_attestation_verification, "verification_status", "UNKNOWN")
        if attestation_verification_status != "PASS":
            actions.append("Latest paper evidence-chain retention custody attestation verification failed; inspect attestation hash, statement hash, and source certification verification digest.")
    if position_reconciliation is not None:
        if position_reconciliation.status == "NO_POSITION_SNAPSHOT":
            actions.append("Capture a paper account/position snapshot with strategy-validator-paper-broker snapshot-account-positions after guarded paper submissions.")
        elif position_reconciliation.status == "PENDING_FILL":
            actions.append("Latest paper submission is not filled yet; refresh account/position snapshot after broker fill status changes.")
        elif position_reconciliation.status == "MISMATCHED":
            actions.append("Investigate broker-state mismatch: latest guarded paper receipt does not reconcile with the position snapshot.")
        elif position_reconciliation.reconciliation_blocker_count:
            actions.append("Review paper account/position reconciliation blockers before trusting paper broker state.")
    if journal_count == 0:
        actions.append("Use strategy-validator-paper-broker dry-run-order or submit-paper-order on a trusted host to materialize paper broker evidence.")
    if not actions:
        actions.append("Paper execution cockpit is populated; continue using CLI-only order submission and review journal evidence.")
    return actions

__all__ = ["_recommended_actions"]
