"""Retention custody chain parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_custody_chain_parsers(sub: argparse._SubParsersAction) -> None:
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
