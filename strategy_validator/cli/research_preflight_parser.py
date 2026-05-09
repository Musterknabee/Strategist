from __future__ import annotations

import argparse


def build_research_preflight_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run semantic research intake preflight without adjudicating or writing the ledger."
    )
    parser.add_argument("--proposal", help="Path to an ExperimentManifest JSON document.")
    parser.add_argument("--artifact", help="Path to a FeatureFactoryArtifact JSON document.")
    parser.add_argument("--published-at", help="Feature publication timestamp, ISO-8601.")
    parser.add_argument("--available-at", help="Feature availability timestamp, ISO-8601.")
    parser.add_argument("--asset-id", default=None, help="Optional asset override; defaults to proposal evidence subject.")
    parser.add_argument("--dataset-id", default="semantic_tribunal_features/v1")
    parser.add_argument("--dry-run", action="store_true", help="Verify without mutating the proposal object in memory.")
    parser.add_argument(
        "--write-updated-proposal",
        default="",
        help="Optional path to write the proposal with attached evidence/Data Spine seal.",
    )
    parser.add_argument(
        "--write-report",
        default="",
        help="Optional path to write the semantic preflight report JSON in addition to stdout.",
    )
    parser.add_argument(
        "--verify-summary-json",
        action="store_true",
        help="Integrity mode only: emit compact operator summary JSON instead of the full issue report.",
    )
    parser.add_argument(
        "--adjudication-gate-summary-json",
        action="store_true",
        help="Integrity mode only: emit the exact compact semantic adjudication-gate summary.",
    )
    parser.add_argument(
        "--adjudication-gate-artifact-json",
        action="store_true",
        help="Integrity mode only: emit the checksummed semantic adjudication-gate artifact.",
    )
    parser.add_argument(
        "--adjudication-readiness-json",
        action="store_true",
        help="Integrity mode only: emit the final semantic adjudication handoff readiness report.",
    )
    parser.add_argument(
        "--adjudication-handoff-artifact-json",
        action="store_true",
        help="Integrity mode only: emit the sealed final semantic adjudication handoff artifact.",
    )
    parser.add_argument(
        "--adjudication-bundle-json",
        action="store_true",
        help="Integrity mode only: emit the compact semantic adjudication bundle.",
    )
    parser.add_argument(
        "--gate-artifact",
        default="",
        help="Optional semantic adjudication-gate artifact JSON to verify while building readiness.",
    )
    parser.add_argument(
        "--handoff-artifact",
        default="",
        help="Optional semantic adjudication-handoff artifact JSON to embed while building a bundle.",
    )
    parser.add_argument(
        "--require-gate-artifact",
        action="store_true",
        help="Readiness mode only: fail the handoff if a semantic lane exists without a gate artifact.",
    )
    parser.add_argument(
        "--verify-gate-artifact",
        default="",
        help="Verify a semantic adjudication-gate artifact JSON, optionally against --verify-proposal-only.",
    )
    parser.add_argument(
        "--verify-handoff-artifact",
        default="",
        help="Verify a semantic adjudication handoff artifact JSON, optionally against --verify-proposal-only.",
    )
    parser.add_argument(
        "--verify-bundle",
        default="",
        help="Verify a semantic adjudication bundle JSON, optionally against --verify-proposal-only.",
    )
    parser.add_argument(
        "--bundle-summary-json",
        action="store_true",
        help="Verification mode only: emit compact semantic adjudication bundle summary JSON.",
    )
    parser.add_argument(
        "--bundle-manifest-json",
        action="store_true",
        help="Verification mode only: emit a portable manifest for --verify-bundle.",
    )
    parser.add_argument(
        "--verify-bundle-manifest",
        default="",
        help="Verify a semantic adjudication bundle manifest JSON, optionally with --verify-bundle and --verify-proposal-only.",
    )
    parser.add_argument(
        "--bundle-release-preflight-json",
        action="store_true",
        help="Verification mode: emit final operator/CI release preflight for --verify-bundle and optional --verify-bundle-manifest.",
    )
    parser.add_argument(
        "--bundle-release-index-json",
        action="store_true",
        help="Verification mode: emit portable release index for --verify-bundle and optional --verify-bundle-manifest.",
    )
    parser.add_argument(
        "--verify-bundle-release-index",
        default="",
        help="Verify a semantic adjudication bundle release index JSON, optionally with --verify-bundle/--verify-bundle-manifest/--verify-proposal-only.",
    )
    parser.add_argument(
        "--release-capsule-json",
        action="store_true",
        help="Verification mode: emit final semantic release capsule for --verify-bundle-release-index and optional source artifacts.",
    )
    parser.add_argument(
        "--verify-release-capsule",
        default="",
        help="Verify a semantic release capsule JSON, optionally with --verify-bundle-release-index/source artifacts.",
    )
    parser.add_argument(
        "--release-capsule-summary-json",
        action="store_true",
        help="Verification mode: emit compact operator/CI summary for --verify-release-capsule.",
    )
    parser.add_argument(
        "--release-decision-record-json",
        action="store_true",
        help="Verification mode: emit terminal operator/CI decision record for --verify-release-capsule.",
    )
    parser.add_argument(
        "--verify-release-decision-record",
        default="",
        help="Verify a terminal semantic release decision record JSON, optionally with --verify-release-capsule/source artifacts.",
    )
    parser.add_argument(
        "--release-decision-record-summary-json",
        action="store_true",
        help="With --verify-release-decision-record: emit compact terminal decision-record summary JSON.",
    )
    parser.add_argument(
        "--release-decision-record",
        action="append",
        default=[],
        help="Path to a semantic release decision record; repeat for ledger generation/verification.",
    )
    parser.add_argument(
        "--release-decision-ledger-json",
        action="store_true",
        help="Emit a chained semantic release decision ledger from --release-decision-record inputs.",
    )
    parser.add_argument(
        "--verify-release-decision-ledger",
        default="",
        help="Path to a semantic release decision ledger JSON document to verify.",
    )
    parser.add_argument(
        "--release-decision-ledger-summary-json",
        action="store_true",
        help="With --verify-release-decision-ledger: emit compact operator/CI decision-ledger summary JSON.",
    )
    parser.add_argument(
        "--release-handoff-certificate-json",
        action="store_true",
        help="With --verify-release-decision-ledger: emit terminal handoff certificate JSON for validator adjudication.",
    )
    parser.add_argument(
        "--verify-release-handoff-certificate",
        default="",
        help="Path to a semantic release handoff certificate JSON document to verify.",
    )
    parser.add_argument(
        "--release-handoff-certificate-summary-json",
        action="store_true",
        help="With --verify-release-handoff-certificate: emit compact terminal handoff certificate summary JSON.",
    )
    parser.add_argument(
        "--release-handoff-certificate-evidence-json",
        action="store_true",
        help="With --verify-release-handoff-certificate: emit validator-facing Evidence wrapping the terminal handoff certificate.",
    )
    parser.add_argument(
        "--verify-release-handoff-certificate-evidence",
        default="",
        help="Path to validator-facing semantic release handoff certificate Evidence JSON to verify.",
    )
    parser.add_argument(
        "--release-handoff-certificate-evidence-summary-json",
        action="store_true",
        help="With --verify-release-handoff-certificate-evidence: emit compact validator handoff Evidence summary JSON.",
    )
    parser.add_argument(
        "--validator-handoff-packet-json",
        action="store_true",
        help="With --verify-release-handoff-certificate-evidence: emit portable validator handoff packet JSON.",
    )
    parser.add_argument(
        "--verify-validator-handoff-packet",
        default="",
        help="Path to portable semantic validator handoff packet JSON to verify.",
    )
    parser.add_argument(
        "--validator-handoff-packet-summary-json",
        action="store_true",
        help="With --verify-validator-handoff-packet: emit compact validator handoff packet summary JSON.",
    )
    parser.add_argument(
        "--validator-handoff-packet-ingress-json",
        action="store_true",
        help="With --verify-validator-handoff-packet: emit pre-adjudication validator-ingress packet report JSON.",
    )
    parser.add_argument(
        "--validator-handoff-packet-ingress-summary-json",
        action="store_true",
        help="With --verify-validator-handoff-packet: emit compact validator-ingress packet summary JSON.",
    )
    parser.add_argument(
        "--validator-handoff-ingress-certificate-json",
        action="store_true",
        help="With --verify-validator-handoff-packet: emit sealed validator-ingress certificate JSON.",
    )
    parser.add_argument(
        "--verify-validator-handoff-ingress-certificate",
        default="",
        help="Path to sealed validator-ingress certificate JSON to verify.",
    )
    parser.add_argument(
        "--validator-handoff-ingress-certificate-summary-json",
        action="store_true",
        help="With --verify-validator-handoff-ingress-certificate: emit compact validator-ingress certificate summary JSON.",
    )
    parser.add_argument(
        "--validator-ingress-acceptance-record-json",
        action="store_true",
        help="With --verify-validator-handoff-ingress-certificate: emit terminal validator-ingress acceptance record JSON.",
    )
    parser.add_argument(
        "--verify-validator-ingress-acceptance-record",
        default="",
        help="Path to terminal semantic validator-ingress acceptance record JSON to verify.",
    )
    parser.add_argument(
        "--validator-ingress-acceptance-record-summary-json",
        action="store_true",
        help="With --verify-validator-ingress-acceptance-record: emit compact terminal acceptance summary JSON.",
    )
    parser.add_argument(
        "--validator-ingress-acceptance-record",
        action="append",
        default=[],
        help="Path to a terminal semantic validator-ingress acceptance record; repeat for acceptance-ledger generation/verification.",
    )
    parser.add_argument(
        "--validator-ingress-acceptance-ledger-json",
        action="store_true",
        help="Emit a chained semantic validator-ingress acceptance ledger from --validator-ingress-acceptance-record inputs.",
    )
    parser.add_argument(
        "--verify-validator-ingress-acceptance-ledger",
        default="",
        help="Path to a semantic validator-ingress acceptance ledger JSON document to verify.",
    )
    parser.add_argument(
        "--validator-ingress-acceptance-ledger-summary-json",
        action="store_true",
        help="With --verify-validator-ingress-acceptance-ledger: emit compact terminal acceptance-ledger summary JSON.",
    )
    parser.add_argument(
        "--validator-submission-packet-json",
        action="store_true",
        help="Emit terminal semantic validator submission packet from --verify-validator-ingress-acceptance-ledger.",
    )
    parser.add_argument(
        "--verify-validator-submission-packet",
        default="",
        help="Path to a terminal semantic validator submission packet JSON document to verify.",
    )
    parser.add_argument(
        "--validator-submission-packet-summary-json",
        action="store_true",
        help="With --verify-validator-submission-packet: emit compact validator submission packet summary JSON.",
    )
    parser.add_argument(
        "--validator-submission-packet-evidence-json",
        action="store_true",
        help="With --verify-validator-submission-packet: emit validator-facing Evidence wrapping the submission packet.",
    )
    parser.add_argument(
        "--verify-validator-submission-packet-evidence",
        default="",
        help="Path to validator-facing Evidence wrapping a semantic validator submission packet.",
    )
    parser.add_argument(
        "--validator-submission-packet-evidence-summary-json",
        action="store_true",
        help="With --verify-validator-submission-packet-evidence: emit compact submission-packet Evidence summary JSON.",
    )
    parser.add_argument(
        "--validator-submission-readiness-json",
        action="store_true",
        help="With --verify-proposal-only: emit final proposal-level semantic validator submission readiness JSON.",
    )
    parser.add_argument(
        "--validator-submission-readiness-summary-json",
        action="store_true",
        help="With --verify-proposal-only: emit compact semantic validator submission readiness summary JSON.",
    )
    parser.add_argument(
        "--allow-missing-submission-packet-evidence",
        action="store_true",
        help="Readiness mode only: warn instead of block when terminal submission-packet Evidence is missing.",
    )
    parser.add_argument(
        "--submitted-by",
        default="operator",
        help="Operator or CI actor recorded on --validator-submission-packet-json.",
    )
    parser.add_argument(
        "--submission-reason",
        default="",
        help="Optional rationale recorded on --validator-submission-packet-json.",
    )
    parser.add_argument(
        "--accepted-by",
        default="operator",
        help="Operator or CI actor recorded on --validator-ingress-acceptance-record-json.",
    )
    parser.add_argument(
        "--acceptance-reason",
        default="",
        help="Optional rationale recorded on --validator-ingress-acceptance-record-json.",
    )
    parser.add_argument(
        "--allow-missing-packet-evidence-on-proposal",
        action="store_true",
        help="Ingress mode only: do not require the packet Evidence to already be attached to --verify-proposal-only.",
    )
    parser.add_argument(
        "--issued-by",
        default="operator",
        help="Operator or CI actor issuing --release-handoff-certificate-json.",
    )
    parser.add_argument(
        "--issue-reason",
        default="",
        help="Optional rationale recorded on --release-handoff-certificate-json.",
    )
    parser.add_argument(
        "--decision",
        default="",
        help="Decision for --release-decision-record-json; defaults from capsule readiness.",
    )
    parser.add_argument(
        "--decided-by",
        default="operator",
        help="Operator or CI actor recorded on --release-decision-record-json.",
    )
    parser.add_argument(
        "--decision-reason",
        default="",
        help="Optional rationale recorded on --release-decision-record-json.",
    )
    parser.add_argument(
        "--allow-missing-bundle-manifest",
        action="store_true",
        help="Release preflight mode only: do not block when --verify-bundle-manifest is omitted.",
    )
    parser.add_argument(
        "--verify-proposal-only",
        default="",
        help="Verify semantic evidence already attached to a proposal and exit without materializing new evidence.",
    )
    parser.add_argument(
        "--allow-missing-semantic-evidence",
        action="store_true",
        help="Integrity mode only: do not fail when no semantic materialization evidence is attached.",
    )
    parser.add_argument(
        "--allow-missing-data-spine-seal",
        action="store_true",
        help="Integrity mode only: do not fail when semantic evidence lacks a bundle Data Spine seal.",
    )
    return parser


__all__ = ["build_research_preflight_parser"]
