"""Retention custody archive/retrieval parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_custody_archive_parsers(sub: argparse._SubParsersAction) -> None:
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
