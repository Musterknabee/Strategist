from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from strategy_validator.application.research_integrity import (
    build_semantic_adjudication_bundle,
    build_semantic_adjudication_bundle_manifest,
    build_semantic_adjudication_bundle_release_preflight,
    build_semantic_adjudication_bundle_release_index,
    build_semantic_adjudication_release_capsule,
    build_semantic_adjudication_handoff_artifact,
    build_semantic_adjudication_readiness_report,
    build_semantic_research_adjudication_gate_summary,
    build_semantic_research_gate_artifact,
    summarize_semantic_research_integrity_report,
    verify_proposal_semantic_research_integrity,
    verify_semantic_adjudication_bundle,
    summarize_semantic_adjudication_bundle,
    verify_semantic_adjudication_bundle_manifest,
    verify_semantic_adjudication_bundle_release_index,
    verify_semantic_adjudication_release_capsule,
    summarize_semantic_adjudication_release_capsule,
    build_semantic_adjudication_release_decision_record,
    verify_semantic_adjudication_release_decision_record,
    summarize_semantic_adjudication_release_decision_record,
    build_semantic_adjudication_release_decision_ledger,
    verify_semantic_adjudication_release_decision_ledger,
    summarize_semantic_adjudication_release_decision_ledger,
    build_semantic_adjudication_release_handoff_certificate,
    verify_semantic_adjudication_release_handoff_certificate,
    summarize_semantic_adjudication_release_handoff_certificate,
    build_semantic_release_handoff_certificate_evidence,
    verify_semantic_release_handoff_certificate_evidence,
    summarize_semantic_release_handoff_certificate_evidence,
    build_semantic_validator_handoff_packet,
    verify_semantic_validator_handoff_packet,
    summarize_semantic_validator_handoff_packet,
    build_semantic_validator_handoff_packet_ingress_report,
    summarize_semantic_validator_handoff_packet_ingress,
    build_semantic_validator_handoff_packet_ingress_certificate,
    verify_semantic_validator_handoff_packet_ingress_certificate,
    summarize_semantic_validator_handoff_packet_ingress_certificate,
    build_semantic_validator_ingress_acceptance_record,
    verify_semantic_validator_ingress_acceptance_record,
    summarize_semantic_validator_ingress_acceptance_record,
    build_semantic_validator_ingress_acceptance_ledger,
    verify_semantic_validator_ingress_acceptance_ledger,
    summarize_semantic_validator_ingress_acceptance_ledger,
    build_semantic_validator_submission_packet,
    verify_semantic_validator_submission_packet,
    summarize_semantic_validator_submission_packet,
    build_semantic_validator_submission_packet_evidence,
    verify_semantic_validator_submission_packet_evidence,
    summarize_semantic_validator_submission_packet_evidence,
    build_semantic_validator_submission_readiness_report,
    summarize_semantic_validator_submission_readiness,
    verify_semantic_adjudication_handoff_artifact,
    verify_semantic_research_gate_artifact,
)
from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.evidence import Evidence
from strategy_validator.contracts.semantic import (
    FeatureFactoryArtifact,
    SemanticAdjudicationBundle,
    SemanticAdjudicationBundleManifest,
    SemanticAdjudicationBundleReleaseIndex,
    SemanticAdjudicationReleaseCapsule,
    SemanticAdjudicationReleaseDecisionRecord,
    SemanticAdjudicationReleaseDecisionLedger,
    SemanticAdjudicationReleaseHandoffCertificate,
    SemanticValidatorHandoffPacket,
    SemanticValidatorHandoffPacketIngressCertificate,
    SemanticValidatorIngressAcceptanceRecord,
    SemanticValidatorIngressAcceptanceLedger,
    SemanticValidatorSubmissionPacket,
    SemanticAdjudicationHandoffArtifact,
    SemanticResearchGateArtifact,
)
from strategy_validator.cli.research_preflight_common import _read_json, _write_json


def _require_preflight_args(ns: argparse.Namespace) -> None:
    missing = [
        name
        for name, value in {
            "--proposal": ns.proposal,
            "--artifact": ns.artifact,
            "--published-at": ns.published_at,
            "--available-at": ns.available_at,
        }.items()
        if not value
    ]
    if missing:
        raise SystemExit("missing required preflight arguments: " + ", ".join(missing))


__all__ = ['_require_preflight_args']
