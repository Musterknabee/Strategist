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


def _run_release_capsule_mode(ns: argparse.Namespace) -> int:
    index = SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    capsule = build_semantic_adjudication_release_capsule(
        index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = capsule.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if capsule.ready_for_adjudication else 1


def _run_release_capsule_verification_mode(ns: argparse.Namespace) -> int:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(_read_json(ns.verify_release_capsule))
    index = (
        SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
        if ns.verify_bundle_release_index
        else None
    )
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_adjudication_release_capsule(
        capsule,
        index=index,
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


def _run_release_capsule_summary_mode(ns: argparse.Namespace) -> int:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(_read_json(ns.verify_release_capsule))
    index = (
        SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
        if ns.verify_bundle_release_index
        else None
    )
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    summary = summarize_semantic_adjudication_release_capsule(
        capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.ready_for_adjudication else 1


def _run_release_decision_record_mode(ns: argparse.Namespace) -> int:
    capsule = SemanticAdjudicationReleaseCapsule.model_validate(_read_json(ns.verify_release_capsule))
    index = (
        SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
        if ns.verify_bundle_release_index
        else None
    )
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    record = build_semantic_adjudication_release_decision_record(
        capsule,
        decision=ns.decision or None,
        decided_by=ns.decided_by,
        decision_reason=ns.decision_reason or None,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = record.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if record.decision_allowed else 1


def _run_release_decision_record_verification_mode(ns: argparse.Namespace) -> int:
    record = SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(ns.verify_release_decision_record))
    capsule = (
        SemanticAdjudicationReleaseCapsule.model_validate(_read_json(ns.verify_release_capsule))
        if ns.verify_release_capsule
        else None
    )
    index = (
        SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
        if ns.verify_bundle_release_index
        else None
    )
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_adjudication_release_decision_record(
        record,
        capsule=capsule,
        index=index,
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


def _run_release_decision_record_summary_mode(ns: argparse.Namespace) -> int:
    record = SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(ns.verify_release_decision_record))
    capsule = (
        SemanticAdjudicationReleaseCapsule.model_validate(_read_json(ns.verify_release_capsule))
        if ns.verify_release_capsule
        else None
    )
    index = (
        SemanticAdjudicationBundleReleaseIndex.model_validate(_read_json(ns.verify_bundle_release_index))
        if ns.verify_bundle_release_index
        else None
    )
    bundle = SemanticAdjudicationBundle.model_validate(_read_json(ns.verify_bundle)) if ns.verify_bundle else None
    manifest = (
        SemanticAdjudicationBundleManifest.model_validate(_read_json(ns.verify_bundle_manifest))
        if ns.verify_bundle_manifest
        else None
    )
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    summary = summarize_semantic_adjudication_release_decision_record(
        record,
        capsule=capsule,
        index=index,
        bundle=bundle,
        manifest=manifest,
        proposal=proposal,
        require_manifest=not ns.allow_missing_bundle_manifest,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_TO_VALIDATOR_ADJUDICATION" else 1


def _run_release_decision_ledger_mode(ns: argparse.Namespace) -> int:
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    ledger = build_semantic_adjudication_release_decision_ledger(records)
    payload = ledger.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if ledger.entry_count > 0 else 1


def _run_release_decision_ledger_verification_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(_read_json(ns.verify_release_decision_ledger))
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    report = verify_semantic_adjudication_release_decision_ledger(
        ledger,
        records=records or None,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


def _run_release_decision_ledger_summary_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(_read_json(ns.verify_release_decision_ledger))
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    summary = summarize_semantic_adjudication_release_decision_ledger(
        ledger,
        records=records or None,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_TERMINAL_DECISION_TO_VALIDATOR" else 1


def _run_release_handoff_certificate_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticAdjudicationReleaseDecisionLedger.model_validate(_read_json(ns.verify_release_decision_ledger))
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    certificate = build_semantic_adjudication_release_handoff_certificate(
        ledger,
        records=records or None,
        issued_by=ns.issued_by,
        issue_reason=ns.issue_reason or None,
    )
    payload = certificate.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if certificate.handoff_allowed else 1


def _run_release_handoff_certificate_verification_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(_read_json(ns.verify_release_handoff_certificate))
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(_read_json(ns.verify_release_decision_ledger))
        if ns.verify_release_decision_ledger
        else None
    )
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    report = verify_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records or None,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified and report.handoff_allowed else 1


def _run_release_handoff_certificate_summary_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(_read_json(ns.verify_release_handoff_certificate))
    ledger = (
        SemanticAdjudicationReleaseDecisionLedger.model_validate(_read_json(ns.verify_release_decision_ledger))
        if ns.verify_release_decision_ledger
        else None
    )
    records = [
        SemanticAdjudicationReleaseDecisionRecord.model_validate(_read_json(path))
        for path in (ns.release_decision_record or [])
    ]
    summary = summarize_semantic_adjudication_release_handoff_certificate(
        certificate,
        ledger=ledger,
        records=records or None,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_TO_VALIDATOR_ADJUDICATION" else 1


def _run_release_handoff_certificate_evidence_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticAdjudicationReleaseHandoffCertificate.model_validate(_read_json(ns.verify_release_handoff_certificate))
    evidence = build_semantic_release_handoff_certificate_evidence(certificate)
    payload = evidence.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if evidence.payload.get("handoff_allowed") is True else 1


def _run_release_handoff_certificate_evidence_verification_mode(ns: argparse.Namespace) -> int:
    evidence = Evidence.model_validate(_read_json(ns.verify_release_handoff_certificate_evidence))
    report = verify_semantic_release_handoff_certificate_evidence(evidence)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified and report.handoff_allowed else 1


def _run_release_handoff_certificate_evidence_summary_mode(ns: argparse.Namespace) -> int:
    evidence = Evidence.model_validate(_read_json(ns.verify_release_handoff_certificate_evidence))
    summary = summarize_semantic_release_handoff_certificate_evidence(evidence)
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_CERTIFICATE_EVIDENCE_TO_VALIDATOR" else 1


__all__ = ['_run_release_capsule_mode', '_run_release_capsule_verification_mode', '_run_release_capsule_summary_mode', '_run_release_decision_record_mode', '_run_release_decision_record_verification_mode', '_run_release_decision_record_summary_mode', '_run_release_decision_ledger_mode', '_run_release_decision_ledger_verification_mode', '_run_release_decision_ledger_summary_mode', '_run_release_handoff_certificate_mode', '_run_release_handoff_certificate_verification_mode', '_run_release_handoff_certificate_summary_mode', '_run_release_handoff_certificate_evidence_mode', '_run_release_handoff_certificate_evidence_verification_mode', '_run_release_handoff_certificate_evidence_summary_mode']
