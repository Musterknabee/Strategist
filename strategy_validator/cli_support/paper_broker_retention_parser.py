"""Retention parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_retention_parsers(sub: argparse._SubParsersAction) -> None:
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
