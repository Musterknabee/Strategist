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


def _run_integrity_mode(ns: argparse.Namespace) -> int:
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only))
    report = verify_proposal_semantic_research_integrity(
        proposal,
        require_semantic_evidence=not ns.allow_missing_semantic_evidence,
        require_data_spine_seal=not ns.allow_missing_data_spine_seal,
    )
    if (ns.gate_artifact or ns.require_gate_artifact) and not (ns.adjudication_readiness_json or ns.adjudication_handoff_artifact_json or ns.adjudication_bundle_json):
        raise SystemExit("--gate-artifact/--require-gate-artifact require --adjudication-readiness-json, --adjudication-handoff-artifact-json, or --adjudication-bundle-json")
    payload: dict[str, Any]
    exit_ok = report.verified
    if ns.adjudication_bundle_json:
        gate_artifact = (
            SemanticResearchGateArtifact.model_validate(_read_json(ns.gate_artifact))
            if ns.gate_artifact
            else None
        )
        handoff_artifact = (
            SemanticAdjudicationHandoffArtifact.model_validate(_read_json(ns.handoff_artifact))
            if ns.handoff_artifact
            else None
        )
        bundle = build_semantic_adjudication_bundle(
            proposal,
            gate_artifact=gate_artifact,
            handoff_artifact=handoff_artifact,
            require_gate_artifact=ns.require_gate_artifact,
            require_semantic_evidence=not ns.allow_missing_semantic_evidence,
            require_data_spine_seal=not ns.allow_missing_data_spine_seal,
        )
        payload = bundle.model_dump(mode="json")
        exit_ok = bundle.handoff_artifact.readiness_report.ready_for_adjudication
    elif ns.adjudication_handoff_artifact_json:
        gate_artifact = (
            SemanticResearchGateArtifact.model_validate(_read_json(ns.gate_artifact))
            if ns.gate_artifact
            else None
        )
        handoff = build_semantic_adjudication_handoff_artifact(
            proposal,
            gate_artifact=gate_artifact,
            require_gate_artifact=ns.require_gate_artifact,
            require_semantic_evidence=not ns.allow_missing_semantic_evidence,
            require_data_spine_seal=not ns.allow_missing_data_spine_seal,
        )
        payload = handoff.model_dump(mode="json")
        exit_ok = handoff.readiness_report.ready_for_adjudication
    elif ns.adjudication_readiness_json:
        gate_artifact = (
            SemanticResearchGateArtifact.model_validate(_read_json(ns.gate_artifact))
            if ns.gate_artifact
            else None
        )
        readiness = build_semantic_adjudication_readiness_report(
            proposal,
            gate_artifact=gate_artifact,
            require_gate_artifact=ns.require_gate_artifact,
            require_semantic_evidence=not ns.allow_missing_semantic_evidence,
            require_data_spine_seal=not ns.allow_missing_data_spine_seal,
        )
        payload = readiness.model_dump(mode="json")
        exit_ok = readiness.ready_for_adjudication
    elif ns.adjudication_gate_artifact_json:
        payload = build_semantic_research_gate_artifact(
            proposal,
            require_semantic_evidence=not ns.allow_missing_semantic_evidence,
            require_data_spine_seal=not ns.allow_missing_data_spine_seal,
        ).model_dump(mode="json")
    elif ns.adjudication_gate_summary_json:
        payload = build_semantic_research_adjudication_gate_summary(
            proposal,
            require_semantic_evidence=not ns.allow_missing_semantic_evidence,
            require_data_spine_seal=not ns.allow_missing_data_spine_seal,
        ).model_dump(mode="json")
    elif ns.verify_summary_json:
        payload = summarize_semantic_research_integrity_report(report)
    else:
        payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if exit_ok else 1


def _run_gate_artifact_verification_mode(ns: argparse.Namespace) -> int:
    artifact = SemanticResearchGateArtifact.model_validate(_read_json(ns.verify_gate_artifact))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_research_gate_artifact(artifact, proposal=proposal)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


def _run_handoff_artifact_verification_mode(ns: argparse.Namespace) -> int:
    artifact = SemanticAdjudicationHandoffArtifact.model_validate(_read_json(ns.verify_handoff_artifact))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_adjudication_handoff_artifact(artifact, proposal=proposal)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


def _run_bundle_verification_mode(ns: argparse.Namespace) -> int:
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    if ns.bundle_manifest_json:
        manifest = build_semantic_adjudication_bundle_manifest(bundle, proposal=proposal)
        payload = manifest.model_dump(mode="json")
        exit_ok = manifest.summary.ready_for_adjudication
    elif ns.bundle_summary_json:
        summary = summarize_semantic_adjudication_bundle(bundle, proposal=proposal)
        payload = summary.model_dump(mode="json")
        exit_ok = summary.ready_for_adjudication
    else:
        report = verify_semantic_adjudication_bundle(bundle, proposal=proposal)
        payload = report.model_dump(mode="json")
        exit_ok = report.verified
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if exit_ok else 1


def _run_bundle_manifest_verification_mode(ns: argparse.Namespace) -> int:
    manifest = SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_adjudication_bundle_manifest(manifest, bundle=bundle, proposal=proposal)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


def _run_bundle_release_preflight_mode(ns: argparse.Namespace) -> int:
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle))
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = build_semantic_adjudication_bundle_release_preflight(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.ready_for_adjudication else 1


def _run_bundle_release_index_mode(ns: argparse.Namespace) -> int:
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle))
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    index = build_semantic_adjudication_bundle_release_index(
        bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = index.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if index.release_preflight.ready_for_adjudication else 1


def _run_bundle_release_index_verification_mode(ns: argparse.Namespace) -> int:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_adjudication_bundle_release_index(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


__all__ = ['_run_integrity_mode', '_run_gate_artifact_verification_mode', '_run_handoff_artifact_verification_mode', '_run_bundle_verification_mode', '_run_bundle_manifest_verification_mode', '_run_bundle_release_preflight_mode', '_run_bundle_release_index_mode', '_run_bundle_release_index_verification_mode']
