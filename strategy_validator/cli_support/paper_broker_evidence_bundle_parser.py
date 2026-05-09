"""Evidence bundle parser registration for the paper broker CLI."""
from __future__ import annotations

import argparse
from pathlib import Path


def register_evidence_bundle_parsers(sub: argparse._SubParsersAction) -> None:
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
