"""CLI: Alpaca paper broker evidence (optional keys; no browser orders)."""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from strategy_validator.brokers.alpaca_paper import (
    dry_run_paper_order,
    get_alpaca_paper_account,
    get_alpaca_paper_order_status,
    list_alpaca_paper_positions,
    submit_paper_order,
)
from strategy_validator.brokers.paper_broker_status_builder import (
    build_paper_broker_status_artifact,
    write_paper_broker_status_artifact,
)
from strategy_validator.application.paper_execution_evidence_bundle import write_paper_execution_evidence_bundle_artifact
from strategy_validator.application.paper_execution_evidence_bundle_verification import write_paper_execution_evidence_bundle_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_drift import write_paper_execution_evidence_bundle_drift_artifact
from strategy_validator.application.paper_execution_evidence_bundle_rotation import write_paper_execution_evidence_bundle_rotation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_rotation_execution import write_paper_execution_evidence_bundle_rotation_execution_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation import write_paper_execution_evidence_bundle_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_attestation_verification import write_paper_execution_evidence_bundle_attestation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure import write_paper_execution_evidence_bundle_closure_artifact
from strategy_validator.application.paper_execution_evidence_bundle_closure_verification import write_paper_execution_evidence_bundle_closure_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export import write_paper_execution_evidence_bundle_export_manifest_artifact
from strategy_validator.application.paper_execution_evidence_bundle_export_verification import write_paper_execution_evidence_bundle_export_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention import write_paper_execution_evidence_bundle_retention_receipt_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_verification import write_paper_execution_evidence_bundle_retention_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff import write_paper_execution_evidence_bundle_retention_signoff_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_signoff_verification import write_paper_execution_evidence_bundle_retention_signoff_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff import write_paper_execution_evidence_bundle_retention_handoff_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_verification import write_paper_execution_evidence_bundle_retention_handoff_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance import write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_handoff_acceptance_verification import write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register import write_paper_execution_evidence_bundle_retention_custody_register_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_register_verification import write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal import write_paper_execution_evidence_bundle_retention_custody_seal_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_seal_verification import write_paper_execution_evidence_bundle_retention_custody_seal_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit import write_paper_execution_evidence_bundle_retention_custody_audit_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_audit_verification import write_paper_execution_evidence_bundle_retention_custody_audit_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity import write_paper_execution_evidence_bundle_retention_custody_continuity_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_continuity_verification import write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review import write_paper_execution_evidence_bundle_retention_custody_review_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_review_verification import write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal import write_paper_execution_evidence_bundle_retention_custody_renewal_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_renewal_verification import write_paper_execution_evidence_bundle_retention_custody_renewal_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule import write_paper_execution_evidence_bundle_retention_custody_schedule_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_schedule_verification import write_paper_execution_evidence_bundle_retention_custody_schedule_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice import write_paper_execution_evidence_bundle_retention_custody_notice_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_notice_verification import write_paper_execution_evidence_bundle_retention_custody_notice_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment import write_paper_execution_evidence_bundle_retention_custody_acknowledgment_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_acknowledgment_verification import write_paper_execution_evidence_bundle_retention_custody_acknowledgment_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion import write_paper_execution_evidence_bundle_retention_custody_completion_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_completion_verification import write_paper_execution_evidence_bundle_retention_custody_completion_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout import write_paper_execution_evidence_bundle_retention_custody_closeout_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_closeout_verification import write_paper_execution_evidence_bundle_retention_custody_closeout_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive import write_paper_execution_evidence_bundle_retention_custody_archive_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_archive_verification import write_paper_execution_evidence_bundle_retention_custody_archive_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval import write_paper_execution_evidence_bundle_retention_custody_retrieval_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_retrieval_verification import write_paper_execution_evidence_bundle_retention_custody_retrieval_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return import write_paper_execution_evidence_bundle_retention_custody_return_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_return_verification import write_paper_execution_evidence_bundle_retention_custody_return_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit import write_paper_execution_evidence_bundle_retention_custody_redeposit_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_redeposit_verification import write_paper_execution_evidence_bundle_retention_custody_redeposit_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory import write_paper_execution_evidence_bundle_retention_custody_inventory_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_inventory_verification import write_paper_execution_evidence_bundle_retention_custody_inventory_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation import write_paper_execution_evidence_bundle_retention_custody_reconciliation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_reconciliation_verification import write_paper_execution_evidence_bundle_retention_custody_reconciliation_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification import write_paper_execution_evidence_bundle_retention_custody_certification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_certification_verification import write_paper_execution_evidence_bundle_retention_custody_certification_verification_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation import write_paper_execution_evidence_bundle_retention_custody_attestation_artifact
from strategy_validator.application.paper_execution_evidence_bundle_retention_custody_attestation_verification import write_paper_execution_evidence_bundle_retention_custody_attestation_verification_artifact
from strategy_validator.application.paper_execution_intent_selection import (
    read_paper_execution_intent_selection_artifact,
    write_paper_execution_intent_selection_artifact,
)
from strategy_validator.application.paper_execution_journal import write_paper_order_dry_run_artifact
from strategy_validator.application.paper_execution_order_status import (
    broker_order_id_from_submission,
    find_latest_submission_artifact,
    tracking_id_from_submission,
    write_paper_order_status_artifact,
)
from strategy_validator.application.paper_execution_submission_guard import (
    build_paper_submission_guard_snapshot,
    write_paper_order_submission_artifact,
)
from strategy_validator.application.paper_execution_reconciliation import write_paper_account_position_snapshot_artifact
from strategy_validator.application.paper_execution_cockpit import build_ui_paper_execution_cockpit_payload
from strategy_validator.cli.deployment_env_check import parse_env_file
from strategy_validator.contracts.paper_broker import PaperBrokerOrderIntent
from strategy_validator.contracts.paper_execution import PaperExecutionTimelineEntry, PaperExecutionTimelineSummary
def _paper_broker_artifact_root() -> Path:
    return (Path.cwd() / "artifacts" / "paper_broker").resolve()


def _merge_env(env_file: Path | None) -> dict[str, str]:
    base = {k: str(v) for k, v in os.environ.items()}
    if env_file is None:
        return base
    vals, _ = parse_env_file(env_file)
    return {**base, **vals}


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Paper-only Alpaca broker evidence CLI.")
    sub = p.add_subparsers(dest="cmd", required=True)

    s_status = sub.add_parser("status", help="Account snapshot (paper endpoint only).")
    s_status.add_argument("--env-file", default="", type=Path)
    s_status.add_argument("--output-root", default="", type=Path, help="Write paper_broker/latest/paper_broker_status.json")
    s_status.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca account endpoint when policy is PAPER_READY (default: policy only).",
    )
    s_status.add_argument("--json", action="store_true")

    s_pos = sub.add_parser("positions", help="List paper positions.")
    s_pos.add_argument("--env-file", default="", type=Path)

    s_snap = sub.add_parser(
        "snapshot-account-positions",
        help="Persist a secret-free paper account/position snapshot artifact for reconciliation.",
    )
    s_snap.add_argument("--env-file", default="", type=Path)
    s_snap.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca paper account and positions. Without this flag, writes policy/account hints only.",
    )
    s_snap.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write snapshot evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_select = sub.add_parser("select-intent", help="Persist a paper-only execution intent selection artifact.")
    s_select.add_argument("--tracking-id", required=True)
    s_select.add_argument("--symbol", default="SPY")
    s_select.add_argument("--qty", type=float, default=1.0)
    s_select.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_select.add_argument("--strategy-id", default="")
    s_select.add_argument("--selected-by", default="operator")
    s_select.add_argument("--reason", default="manual paper dry-run preparation")
    s_select.add_argument("--source-artifact", default="")
    s_select.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write selected intent under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_dry = sub.add_parser("dry-run-order", help="Validate intent without submitting.")
    s_dry.add_argument("--tracking-id", required=True)
    s_dry.add_argument("--symbol", default="SPY")
    s_dry.add_argument("--qty", type=float, default=1.0)
    s_dry.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_dry.add_argument("--env-file", default="", type=Path)
    s_dry.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write dry-run evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_dry.add_argument(
        "--no-artifact",
        action="store_true",
        help="Print validation result only; do not write paper_order_dry_run.json evidence.",
    )

    s_replay = sub.add_parser(
        "dry-run-selected-intent",
        help="Replay the selected paper intent artifact through dry-run validation and persist linked evidence.",
    )
    s_replay.add_argument("--tracking-id", default="", help="Tracking id whose latest selected intent should be replayed.")
    s_replay.add_argument(
        "--selection-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_intent_selection.json path to replay. Overrides --tracking-id.",
    )
    s_replay.add_argument("--env-file", default="", type=Path)
    s_replay.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_sub = sub.add_parser("submit-paper-order", help="Submit order to paper API (CLI only).")
    s_sub.add_argument("--tracking-id", required=True)
    s_sub.add_argument("--symbol", default="SPY")
    s_sub.add_argument("--qty", type=float, default=1.0)
    s_sub.add_argument("--side", default="buy", choices=["buy", "sell"])
    s_sub.add_argument("--confirm-paper", action="store_true", required=True)
    s_sub.add_argument("--env-file", default="", type=Path)
    s_sub.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write guarded submission evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_order_status = sub.add_parser(
        "refresh-order-status",
        help="Persist a read-only paper broker order-status refresh artifact for a guarded submission.",
    )
    s_order_status.add_argument("--tracking-id", default="", help="Tracking id whose latest submission should be refreshed.")
    s_order_status.add_argument("--broker-order-id", default="", help="Explicit broker order id. Defaults to latest submission receipt order id.")
    s_order_status.add_argument("--submission-artifact", default="", type=Path, help="Explicit guarded submission artifact path.")
    s_order_status.add_argument("--env-file", default="", type=Path)
    s_order_status.add_argument(
        "--allow-network",
        action="store_true",
        help="Query Alpaca paper order status. Without this flag, writes a blocked status-refresh artifact.",
    )
    s_order_status.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write paper execution evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_bundle = sub.add_parser(
        "seal-evidence-bundle",
        help="Seal the current paper execution timeline into a digest-anchored evidence bundle.",
    )
    s_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Write bundle evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_bundle = sub.add_parser(
        "verify-evidence-bundle",
        help="Verify a sealed paper execution evidence bundle against its source artifacts.",
    )
    s_verify_bundle.add_argument(
        "--bundle-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle.json path. Defaults to latest sealed bundle.",
    )
    s_verify_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_drift_bundle = sub.add_parser(
        "check-evidence-bundle-drift",
        help="Compare the latest sealed paper evidence bundle against the current execution timeline.",
    )
    s_drift_bundle.add_argument(
        "--bundle-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle.json path. Defaults to latest sealed bundle.",
    )
    s_drift_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write drift evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_rotation_bundle = sub.add_parser(
        "recommend-evidence-bundle-rotation",
        help="Write a recovery recommendation for re-sealing/re-verifying paper evidence bundles.",
    )
    s_rotation_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write rotation evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_rotation_exec = sub.add_parser(
        "run-evidence-bundle-rotation",
        help="Execute the safe local seal/verify/drift-check bundle rotation workflow and write a manifest.",
    )
    s_rotation_exec.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write rotation execution evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_rotation_exec.add_argument(
        "--force",
        action="store_true",
        help="Run the seal/verify/drift-check sequence even when the current recommendation says rotation is not needed.",
    )

    s_attest_bundle = sub.add_parser(
        "attest-evidence-bundle",
        help="Write a keyless local DSSE-style attestation envelope for the verified, in-sync paper evidence bundle.",
    )
    s_attest_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write attestation evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_attest_bundle.add_argument(
        "--signer-identity",
        default="local-operator-keyless-stub",
        help="Non-secret signer identity string for the keyless local stub envelope.",
    )

    s_verify_attestation = sub.add_parser(
        "verify-evidence-bundle-attestation",
        help="Verify the keyless local paper evidence-bundle attestation envelope and referenced artifact links.",
    )
    s_verify_attestation.add_argument(
        "--attestation-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_attestation.json path. Defaults to latest attestation.",
    )
    s_verify_attestation.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write attestation verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_close_bundle = sub.add_parser(
        "close-evidence-bundle",
        help="Write a final read-only closure packet for the paper evidence-bundle chain.",
    )
    s_close_bundle.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write closure evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_closure = sub.add_parser(
        "verify-evidence-bundle-closure",
        help="Verify a paper evidence-bundle closure packet and every referenced artifact link.",
    )
    s_verify_closure.add_argument(
        "--closure-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_closure.json path. Defaults to latest closure packet.",
    )
    s_verify_closure.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write closure verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_export_chain = sub.add_parser(
        "export-evidence-bundle-chain",
        help="Write a read-only export handoff manifest for a verified paper evidence-bundle chain.",
    )
    s_export_chain.add_argument(
        "--closure-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_closure_verification.json path. Defaults to latest closure verification.",
    )
    s_export_chain.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write export handoff evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_export = sub.add_parser(
        "verify-evidence-bundle-export",
        help="Verify a paper evidence-chain export handoff manifest and every retained artifact entry.",
    )
    s_verify_export.add_argument(
        "--export-manifest-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_export_manifest.json path. Defaults to latest export manifest.",
    )
    s_verify_export.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write export verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_retention_receipt = sub.add_parser(
        "receipt-evidence-bundle-retention",
        help="Write a read-only retention receipt for a verified paper evidence-chain export handoff.",
    )
    s_retention_receipt.add_argument(
        "--export-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_export_verification.json path. Defaults to latest export verification.",
    )
    s_retention_receipt.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention receipt evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention = sub.add_parser(
        "verify-evidence-bundle-retention",
        help="Verify a paper evidence-chain retention receipt and every retained artifact file digest/size.",
    )
    s_verify_retention.add_argument(
        "--retention-receipt-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_receipt.json path. Defaults to latest retention receipt.",
    )
    s_verify_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_signoff_retention = sub.add_parser(
        "signoff-evidence-bundle-retention",
        help="Write a read-only operator signoff certificate for verified paper evidence-chain retention.",
    )
    s_signoff_retention.add_argument(
        "--retention-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_verification.json path. Defaults to latest retention verification.",
    )
    s_signoff_retention.add_argument("--operator-id", default="operator", help="Operator label to record in the read-only signoff certificate.")
    s_signoff_retention.add_argument("--decision-note", default="", help="Optional short operator decision note to embed in the signoff statement.")
    s_signoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention signoff evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_signoff_retention = sub.add_parser(
        "verify-evidence-bundle-retention-signoff",
        help="Verify a paper evidence-chain retention signoff certificate and referenced retention verification digest.",
    )
    s_verify_signoff_retention.add_argument(
        "--retention-signoff-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_signoff.json path. Defaults to latest retention signoff.",
    )
    s_verify_signoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention signoff verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_handoff_retention = sub.add_parser(
        "handoff-evidence-bundle-retention",
        help="Write a final read-only custody handoff capsule for verified paper evidence-chain retention.",
    )
    s_handoff_retention.add_argument(
        "--retention-signoff-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_signoff_verification.json path. Defaults to latest retention signoff verification.",
    )
    s_handoff_retention.add_argument("--custodian-id", default="operator", help="Custodian label to record in the read-only handoff capsule.")
    s_handoff_retention.add_argument("--handoff-note", default="", help="Optional short custody handoff note to embed in the handoff statement.")
    s_handoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention handoff evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_handoff_retention = sub.add_parser(
        "verify-evidence-bundle-retention-handoff",
        help="Verify a paper evidence-chain retention handoff capsule and referenced signoff-verification digest.",
    )
    s_verify_handoff_retention.add_argument(
        "--retention-handoff-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_handoff.json path. Defaults to latest retention handoff.",
    )
    s_verify_handoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention handoff verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )


    s_accept_handoff_retention = sub.add_parser(
        "accept-evidence-bundle-retention-handoff",
        help="Write a read-only custodian acceptance certificate for verified paper evidence-chain handoff.",
    )
    s_accept_handoff_retention.add_argument(
        "--retention-handoff-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_handoff_verification.json path. Defaults to latest handoff verification.",
    )
    s_accept_handoff_retention.add_argument("--accepting-custodian-id", default="operator", help="Custodian identity recorded in the read-only acceptance certificate.")
    s_accept_handoff_retention.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the acceptance certificate.")
    s_accept_handoff_retention.add_argument("--acceptance-note", default="", help="Optional short acceptance note.")
    s_accept_handoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write handoff acceptance evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_accept_handoff_retention = sub.add_parser(
        "verify-evidence-bundle-retention-handoff-acceptance",
        help="Verify a paper evidence-chain retention handoff acceptance certificate.",
    )
    s_verify_accept_handoff_retention.add_argument(
        "--retention-handoff-acceptance-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_handoff_acceptance.json path. Defaults to latest handoff acceptance.",
    )
    s_verify_accept_handoff_retention.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write handoff acceptance verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_register_retention_custody = sub.add_parser(
        "register-evidence-bundle-retention-custody",
        help="Write a read-only custody register entry for verified paper evidence-chain handoff acceptance.",
    )
    s_register_retention_custody.add_argument(
        "--retention-handoff-acceptance-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_handoff_acceptance_verification.json path. Defaults to latest acceptance verification.",
    )
    s_register_retention_custody.add_argument("--registered-by", default="operator", help="Operator identity recorded in the custody register.")
    s_register_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody register.")
    s_register_retention_custody.add_argument("--register-note", default="", help="Optional short custody register note.")
    s_register_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody register evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_register = sub.add_parser(
        "verify-evidence-bundle-retention-custody-register",
        help="Verify a paper evidence-chain retention custody register entry.",
    )
    s_verify_retention_custody_register.add_argument(
        "--retention-custody-register-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_register.json path. Defaults to latest custody register.",
    )
    s_verify_retention_custody_register.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody register verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_seal_retention_custody = sub.add_parser(
        "seal-evidence-bundle-retention-custody",
        help="Write a read-only final seal for verified paper evidence-chain retention custody.",
    )
    s_seal_retention_custody.add_argument(
        "--retention-custody-register-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_register_verification.json path. Defaults to latest custody register verification.",
    )
    s_seal_retention_custody.add_argument("--sealed-by", default="operator", help="Operator identity recorded in the custody seal.")
    s_seal_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody seal.")
    s_seal_retention_custody.add_argument("--seal-note", default="", help="Optional short custody seal note.")
    s_seal_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody seal evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_seal = sub.add_parser(
        "verify-evidence-bundle-retention-custody-seal",
        help="Verify a paper evidence-chain retention custody seal.",
    )
    s_verify_retention_custody_seal.add_argument(
        "--retention-custody-seal-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_seal.json path. Defaults to latest custody seal.",
    )
    s_verify_retention_custody_seal.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody seal verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_audit_retention_custody = sub.add_parser(
        "audit-evidence-bundle-retention-custody",
        help="Write a read-only custody audit certificate for a verified paper evidence-chain retention custody seal.",
    )
    s_audit_retention_custody.add_argument(
        "--retention-custody-seal-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_seal_verification.json path. Defaults to latest custody seal verification.",
    )
    s_audit_retention_custody.add_argument("--audited-by", default="operator", help="Operator identity recorded in the custody audit certificate.")
    s_audit_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody audit certificate.")
    s_audit_retention_custody.add_argument("--audit-note", default="", help="Optional short custody audit note.")
    s_audit_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody audit evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_audit = sub.add_parser(
        "verify-evidence-bundle-retention-custody-audit",
        help="Verify a paper evidence-chain retention custody audit certificate.",
    )
    s_verify_retention_custody_audit.add_argument(
        "--retention-custody-audit-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_audit.json path. Defaults to latest custody audit.",
    )
    s_verify_retention_custody_audit.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody audit verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_attest_retention_custody_continuity = sub.add_parser(
        "attest-evidence-bundle-retention-custody-continuity",
        help="Write a read-only continuity attestation for a verified paper evidence-chain retention custody audit.",
    )
    s_attest_retention_custody_continuity.add_argument(
        "--retention-custody-audit-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_audit_verification.json path. Defaults to latest custody audit verification.",
    )
    s_attest_retention_custody_continuity.add_argument("--attested-by", default="operator", help="Operator identity recorded in the custody continuity attestation.")
    s_attest_retention_custody_continuity.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody continuity attestation.")
    s_attest_retention_custody_continuity.add_argument("--continuity-note", default="", help="Optional short custody continuity note.")
    s_attest_retention_custody_continuity.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody continuity evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_continuity = sub.add_parser(
        "verify-evidence-bundle-retention-custody-continuity",
        help="Verify a paper evidence-chain retention custody continuity attestation.",
    )
    s_verify_retention_custody_continuity.add_argument(
        "--retention-custody-continuity-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_continuity.json path. Defaults to latest custody continuity attestation.",
    )
    s_verify_retention_custody_continuity.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody continuity verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_review_retention_custody = sub.add_parser(
        "review-evidence-bundle-retention-custody",
        help="Write a read-only review for a verified paper evidence-chain retention custody continuity attestation.",
    )
    s_review_retention_custody.add_argument(
        "--retention-custody-continuity-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_continuity_verification.json path. Defaults to latest custody continuity verification.",
    )
    s_review_retention_custody.add_argument("--reviewed-by", default="operator", help="Operator identity recorded in the custody review.")
    s_review_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody review.")
    s_review_retention_custody.add_argument("--review-note", default="", help="Optional short custody review note.")
    s_review_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody review evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_review = sub.add_parser(
        "verify-evidence-bundle-retention-custody-review",
        help="Verify a paper evidence-chain retention custody review artifact.",
    )
    s_verify_retention_custody_review.add_argument(
        "--retention-custody-review-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_review.json path. Defaults to latest custody review.",
    )
    s_verify_retention_custody_review.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody review verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_renew_retention_custody = sub.add_parser(
        "renew-evidence-bundle-retention-custody",
        help="Write a read-only renewal certificate for a verified paper evidence-chain retention custody review.",
    )
    s_renew_retention_custody.add_argument(
        "--retention-custody-review-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_review_verification.json path. Defaults to latest custody review verification.",
    )
    s_renew_retention_custody.add_argument("--renewed-by", default="operator", help="Operator identity recorded in the custody renewal.")
    s_renew_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal.")
    s_renew_retention_custody.add_argument("--renewal-interval-days", type=int, default=30, help="Number of days until the next custody renewal is due.")
    s_renew_retention_custody.add_argument("--renewal-note", default="", help="Optional short custody renewal note.")
    s_renew_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody renewal evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_renewal = sub.add_parser(
        "verify-evidence-bundle-retention-custody-renewal",
        help="Verify a paper evidence-chain retention custody renewal artifact.",
    )
    s_verify_retention_custody_renewal.add_argument(
        "--retention-custody-renewal-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_renewal.json path. Defaults to latest custody renewal.",
    )
    s_verify_retention_custody_renewal.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody renewal verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_schedule_retention_custody = sub.add_parser(
        "schedule-evidence-bundle-retention-custody-renewal",
        help="Write a read-only schedule for the next verified paper evidence-chain retention custody renewal.",
    )
    s_schedule_retention_custody.add_argument(
        "--retention-custody-renewal-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_renewal_verification.json path. Defaults to latest custody renewal verification.",
    )
    s_schedule_retention_custody.add_argument("--scheduled-by", default="operator", help="Operator identity recorded in the custody renewal schedule.")
    s_schedule_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal schedule.")
    s_schedule_retention_custody.add_argument("--reminder-days-before-due", type=int, default=7, help="Reminder lead time before the next custody renewal due date.")
    s_schedule_retention_custody.add_argument("--schedule-note", default="", help="Optional short custody schedule note.")
    s_schedule_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody schedule evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_schedule = sub.add_parser(
        "verify-evidence-bundle-retention-custody-schedule",
        help="Verify a paper evidence-chain retention custody renewal schedule artifact.",
    )
    s_verify_retention_custody_schedule.add_argument(
        "--retention-custody-schedule-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_schedule.json path. Defaults to latest custody renewal schedule.",
    )
    s_verify_retention_custody_schedule.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody schedule verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_notice_retention_custody = sub.add_parser(
        "notice-evidence-bundle-retention-custody-renewal",
        help="Write a read-only operator notice for a verified paper evidence-chain retention custody renewal schedule.",
    )
    s_notice_retention_custody.add_argument(
        "--retention-custody-schedule-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_schedule_verification.json path. Defaults to latest custody renewal schedule verification.",
    )
    s_notice_retention_custody.add_argument("--notified-by", default="operator", help="Operator identity recorded in the custody renewal notice.")
    s_notice_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal notice.")
    s_notice_retention_custody.add_argument("--notice-note", default="", help="Optional short custody renewal notice note.")
    s_notice_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody notice evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_notice = sub.add_parser(
        "verify-evidence-bundle-retention-custody-notice",
        help="Verify a paper evidence-chain retention custody renewal notice artifact.",
    )
    s_verify_retention_custody_notice.add_argument(
        "--retention-custody-notice-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_notice.json path. Defaults to latest custody renewal notice.",
    )
    s_verify_retention_custody_notice.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody notice verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )


    s_ack_retention_custody_notice = sub.add_parser(
        "acknowledge-evidence-bundle-retention-custody-notice",
        help="Write a read-only operator acknowledgment for a verified paper evidence-chain retention custody renewal notice.",
    )
    s_ack_retention_custody_notice.add_argument(
        "--retention-custody-notice-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_notice_verification.json path. Defaults to latest custody renewal notice verification.",
    )
    s_ack_retention_custody_notice.add_argument("--acknowledged-by", default="operator", help="Operator identity recorded in the custody renewal notice acknowledgment.")
    s_ack_retention_custody_notice.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal notice acknowledgment.")
    s_ack_retention_custody_notice.add_argument("--acknowledgment-note", default="", help="Optional short custody renewal notice acknowledgment note.")
    s_ack_retention_custody_notice.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody acknowledgment evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_acknowledgment = sub.add_parser(
        "verify-evidence-bundle-retention-custody-acknowledgment",
        help="Verify a paper evidence-chain retention custody renewal notice acknowledgment artifact.",
    )
    s_verify_retention_custody_acknowledgment.add_argument(
        "--retention-custody-acknowledgment-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_acknowledgment.json path. Defaults to latest custody renewal notice acknowledgment.",
    )
    s_verify_retention_custody_acknowledgment.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody acknowledgment verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_complete_retention_custody_renewal = sub.add_parser(
        "complete-evidence-bundle-retention-custody-renewal",
        help="Write a read-only completion record for an acknowledged paper evidence-chain retention custody renewal.",
    )
    s_complete_retention_custody_renewal.add_argument(
        "--retention-custody-acknowledgment-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_acknowledgment_verification.json path. Defaults to latest custody acknowledgment verification.",
    )
    s_complete_retention_custody_renewal.add_argument("--completed-by", default="operator", help="Operator identity recorded in the custody renewal completion.")
    s_complete_retention_custody_renewal.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody renewal completion.")
    s_complete_retention_custody_renewal.add_argument("--completion-note", default="", help="Optional short custody renewal completion note.")
    s_complete_retention_custody_renewal.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody completion evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_completion = sub.add_parser(
        "verify-evidence-bundle-retention-custody-completion",
        help="Verify a paper evidence-chain retention custody completion artifact.",
    )
    s_verify_retention_custody_completion.add_argument(
        "--retention-custody-completion-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_completion.json path. Defaults to latest custody completion.",
    )
    s_verify_retention_custody_completion.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody completion verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_closeout_retention_custody = sub.add_parser(
        "closeout-evidence-bundle-retention-custody-renewal",
        help="Write a read-only closeout record for a verified paper evidence-chain retention custody renewal completion.",
    )
    s_closeout_retention_custody.add_argument(
        "--retention-custody-completion-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_completion_verification.json path. Defaults to latest custody completion verification.",
    )
    s_closeout_retention_custody.add_argument("--closed-out-by", default="operator", help="Operator identity recorded in the custody closeout.")
    s_closeout_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody closeout.")
    s_closeout_retention_custody.add_argument("--closeout-note", default="", help="Optional short custody closeout note.")
    s_closeout_retention_custody.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody closeout evidence under this paper_broker root (default: artifacts/paper_broker).",
    )

    s_verify_retention_custody_closeout = sub.add_parser(
        "verify-evidence-bundle-retention-custody-closeout",
        help="Verify a paper evidence-chain retention custody closeout artifact.",
    )
    s_verify_retention_custody_closeout.add_argument(
        "--retention-custody-closeout-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_closeout.json path. Defaults to latest custody closeout.",
    )
    s_verify_retention_custody_closeout.add_argument(
        "--output-root",
        default="",
        type=Path,
        help="Read/write retention custody closeout verification evidence under this paper_broker root (default: artifacts/paper_broker).",
    )
    s_archive_retention_custody = sub.add_parser(
        "archive-evidence-bundle-retention-custody-closeout",
        help="Write a read-only archive record for a verified paper evidence-chain retention custody closeout.",
    )
    s_archive_retention_custody.add_argument(
        "--retention-custody-closeout-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_closeout_verification.json path. Defaults to latest custody closeout verification.",
    )
    s_archive_retention_custody.add_argument("--archived-by", default="operator", help="Operator identity recorded in the custody archive.")
    s_archive_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody archive.")
    s_archive_retention_custody.add_argument("--archive-note", default="", help="Optional short custody archive note.")
    s_archive_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody archive evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_archive = sub.add_parser(
        "verify-evidence-bundle-retention-custody-archive",
        help="Verify a paper evidence-chain retention custody archive artifact.",
    )
    s_verify_retention_custody_archive.add_argument(
        "--retention-custody-archive-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_archive.json path. Defaults to latest custody archive.",
    )
    s_verify_retention_custody_archive.add_argument("--output-root", default="", type=Path, help="Read/write retention custody archive verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_retrieve_retention_custody = sub.add_parser(
        "retrieve-evidence-bundle-retention-custody-archive",
        help="Write a read-only retrieval record for a verified archived paper evidence-chain retention custody bundle.",
    )
    s_retrieve_retention_custody.add_argument(
        "--retention-custody-archive-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_archive_verification.json path. Defaults to latest custody archive verification.",
    )
    s_retrieve_retention_custody.add_argument("--retrieved-by", default="operator", help="Operator identity recorded in the custody retrieval.")
    s_retrieve_retention_custody.add_argument("--retrieval-purpose", default="operator review", help="Declared read-only retrieval purpose.")
    s_retrieve_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody retrieval.")
    s_retrieve_retention_custody.add_argument("--retrieval-note", default="", help="Optional short custody retrieval note.")
    s_retrieve_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody retrieval evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_retrieval = sub.add_parser(
        "verify-evidence-bundle-retention-custody-retrieval",
        help="Verify a paper evidence-chain retention custody retrieval artifact.",
    )
    s_verify_retention_custody_retrieval.add_argument(
        "--retention-custody-retrieval-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_retrieval.json path. Defaults to latest custody retrieval.",
    )
    s_verify_retention_custody_retrieval.add_argument("--output-root", default="", type=Path, help="Read/write retention custody retrieval verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_return_retention_custody = sub.add_parser(
        "return-evidence-bundle-retention-custody-retrieval",
        help="Write a read-only return record for a verified retrieved paper evidence-chain retention custody bundle.",
    )
    s_return_retention_custody.add_argument(
        "--retention-custody-retrieval-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_retrieval_verification.json path. Defaults to latest retrieval verification.",
    )
    s_return_retention_custody.add_argument("--returned-by", default="operator", help="Operator identity recorded in the custody return.")
    s_return_retention_custody.add_argument("--return-reason", default="retrieval complete", help="Declared read-only custody return reason.")
    s_return_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody return.")
    s_return_retention_custody.add_argument("--return-note", default="", help="Optional short custody return note.")
    s_return_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody return evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_return = sub.add_parser(
        "verify-evidence-bundle-retention-custody-return",
        help="Verify a paper evidence-chain retention custody return artifact.",
    )
    s_verify_retention_custody_return.add_argument(
        "--retention-custody-return-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_return.json path. Defaults to latest custody return.",
    )
    s_verify_retention_custody_return.add_argument("--output-root", default="", type=Path, help="Read/write retention custody return verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_redeposit_retention_custody = sub.add_parser(
        "redeposit-evidence-bundle-retention-custody-return",
        help="Write a read-only redeposit record for a verified returned paper evidence-chain retention custody bundle.",
    )
    s_redeposit_retention_custody.add_argument(
        "--retention-custody-return-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_return_verification.json path. Defaults to latest return verification.",
    )
    s_redeposit_retention_custody.add_argument("--redeposited-by", default="operator", help="Operator identity recorded in the custody redeposit.")
    s_redeposit_retention_custody.add_argument("--redeposit-reason", default="return verified", help="Declared read-only custody redeposit reason.")
    s_redeposit_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody redeposit.")
    s_redeposit_retention_custody.add_argument("--redeposit-note", default="", help="Optional short custody redeposit note.")
    s_redeposit_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody redeposit evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_redeposit = sub.add_parser(
        "verify-evidence-bundle-retention-custody-redeposit",
        help="Verify a paper evidence-chain retention custody redeposit artifact.",
    )
    s_verify_retention_custody_redeposit.add_argument(
        "--retention-custody-redeposit-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_redeposit.json path. Defaults to latest custody redeposit.",
    )
    s_verify_retention_custody_redeposit.add_argument("--output-root", default="", type=Path, help="Read/write retention custody redeposit verification evidence under this paper_broker root (default: artifacts/paper_broker).")


    s_inventory_retention_custody = sub.add_parser(
        "inventory-evidence-bundle-retention-custody-redeposit",
        help="Write a read-only inventory record for a verified redeposited paper evidence-chain retention custody bundle.",
    )
    s_inventory_retention_custody.add_argument(
        "--retention-custody-redeposit-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_redeposit_verification.json path. Defaults to latest redeposit verification.",
    )
    s_inventory_retention_custody.add_argument("--inventoried-by", default="operator", help="Operator identity recorded in the custody inventory.")
    s_inventory_retention_custody.add_argument("--inventory-reason", default="redeposit verified", help="Declared read-only custody inventory reason.")
    s_inventory_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody inventory.")
    s_inventory_retention_custody.add_argument("--inventory-note", default="", help="Optional short custody inventory note.")
    s_inventory_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody inventory evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_inventory = sub.add_parser(
        "verify-evidence-bundle-retention-custody-inventory",
        help="Verify a paper evidence-chain retention custody inventory artifact.",
    )
    s_verify_retention_custody_inventory.add_argument(
        "--retention-custody-inventory-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_inventory.json path. Defaults to latest custody inventory.",
    )
    s_verify_retention_custody_inventory.add_argument("--output-root", default="", type=Path, help="Read/write retention custody inventory verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_reconcile_retention_custody = sub.add_parser(
        "reconcile-evidence-bundle-retention-custody-inventory",
        help="Write a read-only reconciliation record for a verified paper evidence-chain retention custody inventory.",
    )
    s_reconcile_retention_custody.add_argument(
        "--retention-custody-inventory-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_inventory_verification.json path. Defaults to latest inventory verification.",
    )
    s_reconcile_retention_custody.add_argument("--reconciled-by", default="operator", help="Operator identity recorded in the custody reconciliation.")
    s_reconcile_retention_custody.add_argument("--reconciliation-reason", default="inventory verification accepted", help="Declared read-only custody reconciliation reason.")
    s_reconcile_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody reconciliation.")
    s_reconcile_retention_custody.add_argument("--reconciliation-note", default="", help="Optional short custody reconciliation note.")
    s_reconcile_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody reconciliation evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_reconciliation = sub.add_parser(
        "verify-evidence-bundle-retention-custody-reconciliation",
        help="Verify a paper evidence-chain retention custody reconciliation artifact.",
    )
    s_verify_retention_custody_reconciliation.add_argument(
        "--retention-custody-reconciliation-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_reconciliation.json path. Defaults to latest custody reconciliation.",
    )
    s_verify_retention_custody_reconciliation.add_argument("--output-root", default="", type=Path, help="Read/write retention custody reconciliation verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_certify_retention_custody = sub.add_parser(
        "certify-evidence-bundle-retention-custody-reconciliation",
        help="Write a read-only certification record for a verified paper evidence-chain retention custody reconciliation.",
    )
    s_certify_retention_custody.add_argument(
        "--retention-custody-reconciliation-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_reconciliation_verification.json path. Defaults to latest reconciliation verification.",
    )
    s_certify_retention_custody.add_argument("--certified-by", default="operator", help="Operator identity recorded in the custody certification.")
    s_certify_retention_custody.add_argument("--certification-reason", default="reconciliation verification accepted", help="Declared read-only custody certification reason.")
    s_certify_retention_custody.add_argument("--custody-location", default="local-retention", help="Custody location label recorded in the custody certification.")
    s_certify_retention_custody.add_argument("--certification-note", default="", help="Optional short custody certification note.")
    s_certify_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody certification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_certification = sub.add_parser(
        "verify-evidence-bundle-retention-custody-certification",
        help="Verify a paper evidence-chain retention custody certification artifact.",
    )
    s_verify_retention_custody_certification.add_argument(
        "--retention-custody-certification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_certification.json path. Defaults to latest custody certification.",
    )
    s_verify_retention_custody_certification.add_argument("--output-root", default="", type=Path, help="Read/write retention custody certification verification evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_attest_retention_custody = sub.add_parser(
        "attest-evidence-bundle-retention-custody-certification",
        help="Write a read-only attestation record for a verified paper evidence-chain retention custody certification.",
    )
    s_attest_retention_custody.add_argument(
        "--retention-custody-certification-verification-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_certification_verification.json path. Defaults to latest certification verification.",
    )
    s_attest_retention_custody.add_argument("--attested-by", default="operator", help="Operator identity recorded in the custody attestation.")
    s_attest_retention_custody.add_argument("--attestation-reason", default="certification verification accepted", help="Declared read-only custody attestation reason.")
    s_attest_retention_custody.add_argument("--attestation-scope", default="paper-execution-retention-custody", help="Attestation scope recorded in the custody attestation.")
    s_attest_retention_custody.add_argument("--attestation-note", default="", help="Optional short custody attestation note.")
    s_attest_retention_custody.add_argument("--output-root", default="", type=Path, help="Read/write retention custody attestation evidence under this paper_broker root (default: artifacts/paper_broker).")

    s_verify_retention_custody_attestation = sub.add_parser(
        "verify-evidence-bundle-retention-custody-attestation",
        help="Verify a paper evidence-chain retention custody attestation artifact.",
    )
    s_verify_retention_custody_attestation.add_argument(
        "--retention-custody-attestation-artifact",
        default="",
        type=Path,
        help="Explicit paper_execution_evidence_bundle_retention_custody_attestation.json path. Defaults to latest custody attestation.",
    )
    s_verify_retention_custody_attestation.add_argument("--output-root", default="", type=Path, help="Read/write retention custody attestation verification evidence under this paper_broker root (default: artifacts/paper_broker).")


    ns = p.parse_args(argv)
    raw_ef = str(getattr(ns, "env_file", "") or "").strip()
    env = _merge_env(Path(raw_ef) if raw_ef else None)

    if ns.cmd == "status":
        out_root = str(getattr(ns, "output_root", "") or "").strip()
        allow_net = bool(getattr(ns, "allow_network", False))
        want_json = bool(getattr(ns, "json", False))
        if out_root:
            art = build_paper_broker_status_artifact(env, allow_network=allow_net)
            path = write_paper_broker_status_artifact(Path(out_root), art)
            payload = {"ok": True, "artifact_path": str(path), "artifact": art.model_dump(mode="json")}
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
            return 0
        acct = get_alpaca_paper_account(env, allow_network=allow_net)
        payload = {"ok": True, "account": acct.model_dump(mode="json")}
        if want_json:
            sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
        else:
            sys.stdout.write(json.dumps(payload, indent=2) + "\n")
        return 0
    if ns.cmd == "positions":
        pol, rows, notes = list_alpaca_paper_positions(env)
        sys.stdout.write(
            json.dumps(
                {"ok": True, "policy": pol.value, "positions": [r.model_dump(mode="json") for r in rows], "notes": notes},
                indent=2,
            )
            + "\n"
        )
        return 0
    if ns.cmd == "snapshot-account-positions":
        allow_net = bool(getattr(ns, "allow_network", False))
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        account = get_alpaca_paper_account(env, allow_network=allow_net)
        notes = list(account.warnings)
        positions = []
        if allow_net:
            pol, rows, pos_notes = list_alpaca_paper_positions(env)
            positions = rows
            notes.extend(pos_notes)
            if account.policy_status.value != pol.value:
                notes.append(f"POSITION_POLICY_STATUS_{pol.value}")
        else:
            notes.append("POSITIONS_PROBE_SKIPPED_ALLOW_NETWORK_FALSE")
        latest_path, history_path, artifact = write_paper_account_position_snapshot_artifact(
            account_status=account,
            positions=positions,
            notes=notes,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": True,
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "policy_status": artifact.policy_status,
                    "position_count": artifact.position_count,
                    "notes": artifact.notes,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0
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
    if ns.cmd == "seal-evidence-bundle":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        cockpit = build_ui_paper_execution_cockpit_payload()
        timeline = [PaperExecutionTimelineEntry.model_validate(row) for row in cockpit.get("execution_timeline", [])]
        timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit.get("execution_timeline_summary") or {})
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_artifact(
            timeline=timeline,
            timeline_summary=timeline_summary,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.bundle_status != "SEALED_BLOCKED",
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "bundle_sha256": artifact.bundle_sha256,
                    "tracking_id": artifact.tracking_id,
                    "trust_banner": artifact.trust_banner,
                    "bundle_status": artifact.bundle_status,
                    "timeline_sequence_status": artifact.timeline_sequence_status,
                    "timeline_event_count": artifact.timeline_event_count,
                    "source_artifact_count": artifact.source_artifact_count,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.bundle_status != "SEALED_BLOCKED" else 2
    if ns.cmd == "verify-evidence-bundle":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_bundle = str(getattr(ns, "bundle_artifact", "") or "").strip()
        if raw_bundle == ".":
            raw_bundle = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_verification_artifact(
            bundle_artifact_path=Path(raw_bundle) if raw_bundle else None,
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
                    "bundle_hash_valid": artifact.bundle_hash_valid,
                    "timeline_source_link_valid": artifact.timeline_source_link_valid,
                    "source_artifact_count": artifact.source_artifact_count,
                    "verified_source_artifact_count": artifact.verified_source_artifact_count,
                    "missing_source_artifact_count": artifact.missing_source_artifact_count,
                    "mismatched_source_artifact_count": artifact.mismatched_source_artifact_count,
                    "source_bundle_declared_sha256": artifact.source_bundle_declared_sha256,
                    "source_bundle_computed_sha256": artifact.source_bundle_computed_sha256,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.verification_status == "PASS" else 2
    if ns.cmd == "check-evidence-bundle-drift":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_bundle = str(getattr(ns, "bundle_artifact", "") or "").strip()
        if raw_bundle == ".":
            raw_bundle = ""
        cockpit = build_ui_paper_execution_cockpit_payload()
        timeline = [PaperExecutionTimelineEntry.model_validate(row) for row in cockpit.get("execution_timeline", [])]
        timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit.get("execution_timeline_summary") or {})
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_drift_artifact(
            current_timeline=timeline,
            current_timeline_summary=timeline_summary,
            bundle_artifact_path=Path(raw_bundle) if raw_bundle else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.drift_status == "IN_SYNC",
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "drift_status": artifact.drift_status,
                    "trust_banner": artifact.trust_banner,
                    "source_bundle_sha256": artifact.source_bundle_sha256,
                    "current_timeline_fingerprint": artifact.current_timeline_fingerprint,
                    "bundled_timeline_fingerprint": artifact.bundled_timeline_fingerprint,
                    "current_source_artifact_count": artifact.current_source_artifact_count,
                    "bundled_source_artifact_count": artifact.bundled_source_artifact_count,
                    "new_source_artifact_count": len(artifact.new_source_artifacts),
                    "removed_source_artifact_count": len(artifact.removed_source_artifacts),
                    "changed_stage_count": artifact.changed_stage_count,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.drift_status == "IN_SYNC" else 2
    if ns.cmd == "recommend-evidence-bundle-rotation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        cockpit = build_ui_paper_execution_cockpit_payload()
        timeline_summary = PaperExecutionTimelineSummary.model_validate(cockpit.get("execution_timeline_summary") or {})
        latest_bundle = cockpit.get("latest_evidence_bundle")
        latest_verification = cockpit.get("latest_evidence_bundle_verification")
        latest_drift = cockpit.get("latest_evidence_bundle_drift")
        from strategy_validator.contracts.paper_execution import (
            PaperExecutionEvidenceBundleDriftView,
            PaperExecutionEvidenceBundleVerificationView,
            PaperExecutionEvidenceBundleView,
        )
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
        from strategy_validator.contracts.paper_execution import PaperExecutionEvidenceBundleRotationView
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
    if ns.cmd == "attest-evidence-bundle":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        signer_identity = str(getattr(ns, "signer_identity", "") or "local-operator-keyless-stub")
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_attestation_artifact(
            output_root=output_root,
            signer_identity=signer_identity,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "attestation_status": artifact.attestation_status,
                    "trust_banner": artifact.trust_banner,
                    "attestation_mode": artifact.attestation_mode,
                    "signature_status": artifact.signature_status,
                    "signer_identity": artifact.signer_identity,
                    "source_bundle_sha256": artifact.source_bundle_sha256,
                    "source_verification_status": artifact.source_verification_status,
                    "source_drift_status": artifact.source_drift_status,
                    "statement_payload_sha256": artifact.statement_payload_sha256,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.attestation_status in {"ATTESTED", "ATTESTED_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-attestation":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_attestation = str(getattr(ns, "attestation_artifact", "") or "").strip()
        if raw_attestation == ".":
            raw_attestation = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_attestation_verification_artifact(
            attestation_artifact_path=Path(raw_attestation) if raw_attestation else None,
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
                    "source_attestation_declared_sha256": artifact.source_attestation_declared_sha256,
                    "source_attestation_computed_sha256": artifact.source_attestation_computed_sha256,
                    "artifact_hash_valid": artifact.artifact_hash_valid,
                    "statement_payload_hash_valid": artifact.statement_payload_hash_valid,
                    "envelope_payload_hash_valid": artifact.envelope_payload_hash_valid,
                    "keyless_stub_signature_valid": artifact.keyless_stub_signature_valid,
                    "source_bundle_hash_valid": artifact.source_bundle_hash_valid,
                    "source_verification_hash_valid": artifact.source_verification_hash_valid,
                    "source_drift_hash_valid": artifact.source_drift_hash_valid,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.verification_status == "PASS" else 2
    if ns.cmd == "close-evidence-bundle":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_closure_artifact(output_root=output_root)
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.closure_status in {"READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "closure_status": artifact.closure_status,
                    "trust_banner": artifact.trust_banner,
                    "source_bundle_sha256": artifact.source_bundle_sha256,
                    "source_bundle_status": artifact.source_bundle_status,
                    "source_verification_status": artifact.source_verification_status,
                    "source_drift_status": artifact.source_drift_status,
                    "source_attestation_status": artifact.source_attestation_status,
                    "source_attestation_verification_status": artifact.source_attestation_verification_status,
                    "closure_reason_codes": artifact.closure_reason_codes,
                    "recommended_operator_sequence": artifact.recommended_operator_sequence,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.closure_status in {"READY_FOR_OPERATOR_REVIEW", "READY_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-closure":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_closure = str(getattr(ns, "closure_artifact", "") or "").strip()
        if raw_closure == ".":
            raw_closure = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_closure_verification_artifact(
            closure_artifact_path=Path(raw_closure) if raw_closure else None,
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
                    "source_closure_declared_sha256": artifact.source_closure_declared_sha256,
                    "source_closure_computed_sha256": artifact.source_closure_computed_sha256,
                    "closure_artifact_hash_valid": artifact.closure_artifact_hash_valid,
                    "source_bundle_hash_valid": artifact.source_bundle_hash_valid,
                    "source_verification_hash_valid": artifact.source_verification_hash_valid,
                    "source_drift_hash_valid": artifact.source_drift_hash_valid,
                    "source_attestation_hash_valid": artifact.source_attestation_hash_valid,
                    "source_attestation_verification_hash_valid": artifact.source_attestation_verification_hash_valid,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.verification_status == "PASS" else 2
    if ns.cmd == "export-evidence-bundle-chain":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_verification = str(getattr(ns, "closure_verification_artifact", "") or "").strip()
        if raw_verification == ".":
            raw_verification = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_export_manifest_artifact(
            closure_verification_artifact_path=Path(raw_verification) if raw_verification else None,
            output_root=output_root,
        )
        sys.stdout.write(
            json.dumps(
                {
                    "ok": artifact.export_status in {"READY_FOR_EXPORT", "READY_RESTRICTED"},
                    "artifact": str(latest_path),
                    "history_artifact": str(history_path),
                    "artifact_sha256": artifact.artifact_sha256,
                    "tracking_id": artifact.tracking_id,
                    "export_status": artifact.export_status,
                    "trust_banner": artifact.trust_banner,
                    "source_closure_verification_status": artifact.source_closure_verification_status,
                    "source_closure_verification_artifact_sha256": artifact.source_closure_verification_artifact_sha256,
                    "closure_verification_artifact_hash_valid": artifact.closure_verification_artifact_hash_valid,
                    "source_closure_status": artifact.source_closure_status,
                    "export_entry_count": artifact.export_entry_count,
                    "export_digest_valid_entry_count": artifact.export_digest_valid_entry_count,
                    "total_size_bytes": artifact.total_size_bytes,
                    "export_index_sha256": artifact.export_index_sha256,
                    "blockers": artifact.blockers,
                    "warnings": artifact.warnings,
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        return 0 if artifact.export_status in {"READY_FOR_EXPORT", "READY_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-export":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_export_manifest = str(getattr(ns, "export_manifest_artifact", "") or "").strip()
        if raw_export_manifest == ".":
            raw_export_manifest = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_export_verification_artifact(
            export_manifest_artifact_path=Path(raw_export_manifest) if raw_export_manifest else None,
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
                    "source_export_manifest_declared_sha256": artifact.source_export_manifest_declared_sha256,
                    "source_export_manifest_computed_sha256": artifact.source_export_manifest_computed_sha256,
                    "source_export_manifest_status": artifact.source_export_manifest_status,
                    "export_manifest_hash_valid": artifact.export_manifest_hash_valid,
                    "export_index_hash_valid": artifact.export_index_hash_valid,
                    "source_export_entry_count": artifact.source_export_entry_count,
                    "recomputed_export_entry_count": artifact.recomputed_export_entry_count,
                    "recomputed_export_digest_valid_entry_count": artifact.recomputed_export_digest_valid_entry_count,
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
    if ns.cmd == "handoff-evidence-bundle-retention":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_signoff_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_artifact(
            retention_signoff_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            custodian_id=str(getattr(ns, "custodian_id", "operator") or "operator"),
            handoff_note=str(getattr(ns, "handoff_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.handoff_status in {"READY_FOR_HANDOFF", "READY_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "handoff_status": artifact.handoff_status,
            "trust_banner": artifact.trust_banner,
            "custodian_id": artifact.custodian_id,
            "source_retention_signoff_verification_declared_sha256": artifact.source_retention_signoff_verification_declared_sha256,
            "source_retention_signoff_verification_status": artifact.source_retention_signoff_verification_status,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "retention_signoff_artifact_hash_valid": artifact.retention_signoff_artifact_hash_valid,
            "signoff_statement_hash_valid": artifact.signoff_statement_hash_valid,
            "retention_verification_artifact_hash_valid": artifact.retention_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "handoff_statement_sha256": artifact.handoff_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.handoff_status in {"READY_FOR_HANDOFF", "READY_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-handoff":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_handoff_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_verification_artifact(
            retention_handoff_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_handoff_declared_sha256": artifact.source_retention_handoff_declared_sha256,
            "source_retention_handoff_computed_sha256": artifact.source_retention_handoff_computed_sha256,
            "source_retention_handoff_status": artifact.source_retention_handoff_status,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "source_retention_signoff_verification_declared_sha256": artifact.source_retention_signoff_verification_declared_sha256,
            "source_retention_signoff_verification_status": artifact.source_retention_signoff_verification_status,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2


    if ns.cmd == "accept-evidence-bundle-retention-handoff":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_handoff_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_acceptance_artifact(
            retention_handoff_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            accepting_custodian_id=str(getattr(ns, "accepting_custodian_id", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            acceptance_note=str(getattr(ns, "acceptance_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.acceptance_status in {"ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "acceptance_status": artifact.acceptance_status,
            "trust_banner": artifact.trust_banner,
            "accepting_custodian_id": artifact.accepting_custodian_id,
            "custody_location": artifact.custody_location,
            "source_retention_handoff_verification_declared_sha256": artifact.source_retention_handoff_verification_declared_sha256,
            "source_retention_handoff_verification_status": artifact.source_retention_handoff_verification_status,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "acceptance_statement_sha256": artifact.acceptance_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.acceptance_status in {"ACCEPTED_FOR_CUSTODY", "ACCEPTED_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-handoff-acceptance":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_handoff_acceptance_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_handoff_acceptance_verification_artifact(
            retention_handoff_acceptance_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_handoff_acceptance_declared_sha256": artifact.source_retention_handoff_acceptance_declared_sha256,
            "source_retention_handoff_acceptance_status": artifact.source_retention_handoff_acceptance_status,
            "retention_handoff_acceptance_artifact_hash_valid": artifact.retention_handoff_acceptance_artifact_hash_valid,
            "acceptance_statement_hash_valid": artifact.acceptance_statement_hash_valid,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2
    if ns.cmd == "register-evidence-bundle-retention-custody":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_handoff_acceptance_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_register_artifact(
            retention_handoff_acceptance_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            registered_by=str(getattr(ns, "registered_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            register_note=str(getattr(ns, "register_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.register_status in {"REGISTERED", "REGISTERED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "register_status": artifact.register_status,
            "trust_banner": artifact.trust_banner,
            "custody_register_id": artifact.custody_register_id,
            "registered_by": artifact.registered_by,
            "custody_location": artifact.custody_location,
            "source_retention_handoff_acceptance_verification_declared_sha256": artifact.source_retention_handoff_acceptance_verification_declared_sha256,
            "source_retention_handoff_acceptance_verification_status": artifact.source_retention_handoff_acceptance_verification_status,
            "retention_handoff_acceptance_verification_artifact_hash_valid": artifact.retention_handoff_acceptance_verification_artifact_hash_valid,
            "retention_handoff_acceptance_artifact_hash_valid": artifact.retention_handoff_acceptance_artifact_hash_valid,
            "acceptance_statement_hash_valid": artifact.acceptance_statement_hash_valid,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "custody_register_statement_sha256": artifact.custody_register_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.register_status in {"REGISTERED", "REGISTERED_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-custody-register":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_register_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_register_verification_artifact(
            retention_custody_register_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_register_declared_sha256": artifact.source_retention_custody_register_declared_sha256,
            "source_retention_custody_register_status": artifact.source_retention_custody_register_status,
            "retention_custody_register_artifact_hash_valid": artifact.retention_custody_register_artifact_hash_valid,
            "custody_register_statement_hash_valid": artifact.custody_register_statement_hash_valid,
            "retention_handoff_acceptance_verification_artifact_hash_valid": artifact.retention_handoff_acceptance_verification_artifact_hash_valid,
            "retention_handoff_acceptance_artifact_hash_valid": artifact.retention_handoff_acceptance_artifact_hash_valid,
            "acceptance_statement_hash_valid": artifact.acceptance_statement_hash_valid,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "seal-evidence-bundle-retention-custody":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_register_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_seal_artifact(
            retention_custody_register_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            sealed_by=str(getattr(ns, "sealed_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            seal_note=str(getattr(ns, "seal_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.seal_status in {"SEALED", "SEALED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "seal_status": artifact.seal_status,
            "trust_banner": artifact.trust_banner,
            "custody_seal_id": artifact.custody_seal_id,
            "sealed_by": artifact.sealed_by,
            "custody_location": artifact.custody_location,
            "source_retention_custody_register_verification_declared_sha256": artifact.source_retention_custody_register_verification_declared_sha256,
            "source_retention_custody_register_verification_status": artifact.source_retention_custody_register_verification_status,
            "retention_custody_register_verification_artifact_hash_valid": artifact.retention_custody_register_verification_artifact_hash_valid,
            "retention_custody_register_artifact_hash_valid": artifact.retention_custody_register_artifact_hash_valid,
            "custody_register_statement_hash_valid": artifact.custody_register_statement_hash_valid,
            "retention_handoff_acceptance_verification_artifact_hash_valid": artifact.retention_handoff_acceptance_verification_artifact_hash_valid,
            "retention_handoff_acceptance_artifact_hash_valid": artifact.retention_handoff_acceptance_artifact_hash_valid,
            "acceptance_statement_hash_valid": artifact.acceptance_statement_hash_valid,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "custody_seal_statement_sha256": artifact.custody_seal_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.seal_status in {"SEALED", "SEALED_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-custody-seal":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_seal_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_seal_verification_artifact(
            retention_custody_seal_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_seal_declared_sha256": artifact.source_retention_custody_seal_declared_sha256,
            "source_retention_custody_seal_status": artifact.source_retention_custody_seal_status,
            "retention_custody_seal_artifact_hash_valid": artifact.retention_custody_seal_artifact_hash_valid,
            "custody_seal_statement_hash_valid": artifact.custody_seal_statement_hash_valid,
            "retention_custody_register_verification_artifact_hash_valid": artifact.retention_custody_register_verification_artifact_hash_valid,
            "retention_custody_register_artifact_hash_valid": artifact.retention_custody_register_artifact_hash_valid,
            "custody_register_statement_hash_valid": artifact.custody_register_statement_hash_valid,
            "retention_handoff_acceptance_verification_artifact_hash_valid": artifact.retention_handoff_acceptance_verification_artifact_hash_valid,
            "retention_handoff_acceptance_artifact_hash_valid": artifact.retention_handoff_acceptance_artifact_hash_valid,
            "acceptance_statement_hash_valid": artifact.acceptance_statement_hash_valid,
            "retention_handoff_verification_artifact_hash_valid": artifact.retention_handoff_verification_artifact_hash_valid,
            "retention_handoff_artifact_hash_valid": artifact.retention_handoff_artifact_hash_valid,
            "handoff_statement_hash_valid": artifact.handoff_statement_hash_valid,
            "retention_signoff_verification_artifact_hash_valid": artifact.retention_signoff_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "audit-evidence-bundle-retention-custody":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_seal_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_audit_artifact(
            retention_custody_seal_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            audited_by=str(getattr(ns, "audited_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            audit_note=str(getattr(ns, "audit_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.audit_status in {"AUDITED", "AUDITED_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "audit_status": artifact.audit_status,
            "trust_banner": artifact.trust_banner,
            "custody_audit_id": artifact.custody_audit_id,
            "audited_by": artifact.audited_by,
            "custody_location": artifact.custody_location,
            "source_retention_custody_seal_verification_declared_sha256": artifact.source_retention_custody_seal_verification_declared_sha256,
            "source_retention_custody_seal_verification_status": artifact.source_retention_custody_seal_verification_status,
            "retention_custody_seal_verification_artifact_hash_valid": artifact.retention_custody_seal_verification_artifact_hash_valid,
            "retention_custody_seal_artifact_hash_valid": artifact.retention_custody_seal_artifact_hash_valid,
            "custody_seal_statement_hash_valid": artifact.custody_seal_statement_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "custody_audit_statement_sha256": artifact.custody_audit_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.audit_status in {"AUDITED", "AUDITED_RESTRICTED"} else 2
    if ns.cmd == "verify-evidence-bundle-retention-custody-audit":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_audit_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_audit_verification_artifact(
            retention_custody_audit_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_audit_declared_sha256": artifact.source_retention_custody_audit_declared_sha256,
            "source_retention_custody_audit_status": artifact.source_retention_custody_audit_status,
            "retention_custody_audit_artifact_hash_valid": artifact.retention_custody_audit_artifact_hash_valid,
            "custody_audit_statement_hash_valid": artifact.custody_audit_statement_hash_valid,
            "retention_custody_seal_verification_artifact_hash_valid": artifact.retention_custody_seal_verification_artifact_hash_valid,
            "retention_custody_seal_artifact_hash_valid": artifact.retention_custody_seal_artifact_hash_valid,
            "custody_seal_statement_hash_valid": artifact.custody_seal_statement_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2


    if ns.cmd == "attest-evidence-bundle-retention-custody-continuity":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_audit_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_continuity_artifact(
            retention_custody_audit_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            attested_by=str(getattr(ns, "attested_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            continuity_note=str(getattr(ns, "continuity_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.continuity_status in {"CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "continuity_status": artifact.continuity_status,
            "trust_banner": artifact.trust_banner,
            "custody_continuity_id": artifact.custody_continuity_id,
            "attested_by": artifact.attested_by,
            "custody_location": artifact.custody_location,
            "source_retention_custody_audit_verification_declared_sha256": artifact.source_retention_custody_audit_verification_declared_sha256,
            "source_retention_custody_audit_verification_status": artifact.source_retention_custody_audit_verification_status,
            "retention_custody_audit_verification_artifact_hash_valid": artifact.retention_custody_audit_verification_artifact_hash_valid,
            "retention_custody_audit_artifact_hash_valid": artifact.retention_custody_audit_artifact_hash_valid,
            "custody_audit_statement_hash_valid": artifact.custody_audit_statement_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "custody_continuity_statement_sha256": artifact.custody_continuity_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.continuity_status in {"CONTINUITY_ATTESTED", "CONTINUITY_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-continuity":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_continuity_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_continuity_verification_artifact(
            retention_custody_continuity_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_continuity_declared_sha256": artifact.source_retention_custody_continuity_declared_sha256,
            "source_retention_custody_continuity_status": artifact.source_retention_custody_continuity_status,
            "retention_custody_continuity_artifact_hash_valid": artifact.retention_custody_continuity_artifact_hash_valid,
            "custody_continuity_statement_hash_valid": artifact.custody_continuity_statement_hash_valid,
            "retention_custody_audit_verification_artifact_hash_valid": artifact.retention_custody_audit_verification_artifact_hash_valid,
            "retention_custody_audit_artifact_hash_valid": artifact.retention_custody_audit_artifact_hash_valid,
            "custody_audit_statement_hash_valid": artifact.custody_audit_statement_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

    if ns.cmd == "review-evidence-bundle-retention-custody":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_continuity_verification_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_review_artifact(
            retention_custody_continuity_verification_artifact_path=Path(raw_source) if raw_source else None,
            output_root=output_root,
            reviewed_by=str(getattr(ns, "reviewed_by", "operator") or "operator"),
            custody_location=str(getattr(ns, "custody_location", "local-retention") or "local-retention"),
            review_note=str(getattr(ns, "review_note", "") or "") or None,
        )
        sys.stdout.write(json.dumps({
            "ok": artifact.review_status in {"REVIEWED", "REVIEW_RESTRICTED"},
            "artifact": str(latest_path),
            "history_artifact": str(history_path),
            "artifact_sha256": artifact.artifact_sha256,
            "tracking_id": artifact.tracking_id,
            "review_status": artifact.review_status,
            "trust_banner": artifact.trust_banner,
            "custody_review_id": artifact.custody_review_id,
            "reviewed_by": artifact.reviewed_by,
            "custody_location": artifact.custody_location,
            "source_retention_custody_continuity_verification_declared_sha256": artifact.source_retention_custody_continuity_verification_declared_sha256,
            "source_retention_custody_continuity_verification_status": artifact.source_retention_custody_continuity_verification_status,
            "retention_custody_continuity_verification_artifact_hash_valid": artifact.retention_custody_continuity_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "custody_review_statement_sha256": artifact.custody_review_statement_sha256,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.review_status in {"REVIEWED", "REVIEW_RESTRICTED"} else 2

    if ns.cmd == "verify-evidence-bundle-retention-custody-review":
        raw_out_root = str(getattr(ns, "output_root", "") or "").strip()
        output_root = Path(raw_out_root) if raw_out_root else None
        raw_source = str(getattr(ns, "retention_custody_review_artifact", "") or "").strip()
        if raw_source == ".":
            raw_source = ""
        latest_path, history_path, artifact = write_paper_execution_evidence_bundle_retention_custody_review_verification_artifact(
            retention_custody_review_artifact_path=Path(raw_source) if raw_source else None,
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
            "source_retention_custody_review_declared_sha256": artifact.source_retention_custody_review_declared_sha256,
            "source_retention_custody_review_status": artifact.source_retention_custody_review_status,
            "retention_custody_review_artifact_hash_valid": artifact.retention_custody_review_artifact_hash_valid,
            "custody_review_statement_hash_valid": artifact.custody_review_statement_hash_valid,
            "retention_custody_continuity_verification_artifact_hash_valid": artifact.retention_custody_continuity_verification_artifact_hash_valid,
            "recomputed_retention_entry_count": artifact.recomputed_retention_entry_count,
            "recomputed_retention_ready_entry_count": artifact.recomputed_retention_ready_entry_count,
            "missing_entry_count": artifact.missing_entry_count,
            "digest_mismatch_entry_count": artifact.digest_mismatch_entry_count,
            "blockers": artifact.blockers,
            "warnings": artifact.warnings,
        }, indent=2, sort_keys=True) + "\n")
        return 0 if artifact.verification_status == "PASS" else 2

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

    return 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
