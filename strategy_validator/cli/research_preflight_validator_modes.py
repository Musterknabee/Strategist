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


def _run_validator_handoff_packet_mode(ns: argparse.Namespace) -> int:
    evidence = Evidence.model_validate(_read_json(ns.verify_release_handoff_certificate_evidence))
    packet = build_semantic_validator_handoff_packet(evidence)
    payload = packet.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if packet.handoff_allowed else 1


def _run_validator_handoff_packet_verification_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet))
    evidence = Evidence.model_validate(_read_json(ns.verify_release_handoff_certificate_evidence)) if ns.verify_release_handoff_certificate_evidence else None
    report = verify_semantic_validator_handoff_packet(packet, evidence=evidence)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified and report.handoff_allowed else 1


def _run_validator_handoff_packet_summary_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet))
    evidence = Evidence.model_validate(_read_json(ns.verify_release_handoff_certificate_evidence)) if ns.verify_release_handoff_certificate_evidence else None
    summary = summarize_semantic_validator_handoff_packet(packet, evidence=evidence)
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_PACKET_TO_VALIDATOR" else 1


def _run_validator_handoff_packet_ingress_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = build_semantic_validator_handoff_packet_ingress_report(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.ready_for_validator_ingress else 1


def _run_validator_handoff_packet_ingress_summary_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    summary = summarize_semantic_validator_handoff_packet_ingress(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.ready_for_validator_ingress else 1


def _run_validator_handoff_packet_ingress_certificate_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet))
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    certificate = build_semantic_validator_handoff_packet_ingress_certificate(
        packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
        issued_by=ns.issued_by,
        issue_reason=ns.issue_reason,
    )
    payload = certificate.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if certificate.ready_for_validator_ingress else 1


def _run_validator_handoff_packet_ingress_certificate_verification_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(_read_json(ns.verify_validator_handoff_ingress_certificate))
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet)) if ns.verify_validator_handoff_packet else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified and report.ready_for_validator_ingress else 1


def _run_validator_handoff_packet_ingress_certificate_summary_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(_read_json(ns.verify_validator_handoff_ingress_certificate))
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet)) if ns.verify_validator_handoff_packet else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    summary = summarize_semantic_validator_handoff_packet_ingress_certificate(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_CERTIFIED_PACKET_EVIDENCE_TO_VALIDATOR" else 1


def _run_validator_ingress_acceptance_record_mode(ns: argparse.Namespace) -> int:
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(_read_json(ns.verify_validator_handoff_ingress_certificate))
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet)) if ns.verify_validator_handoff_packet else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    record = build_semantic_validator_ingress_acceptance_record(
        certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
        accepted_by=ns.accepted_by,
        acceptance_reason=ns.acceptance_reason,
    )
    payload = record.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if record.accepted_for_validator_adjudication else 1


def _run_validator_ingress_acceptance_record_verification_mode(ns: argparse.Namespace) -> int:
    record = SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(ns.verify_validator_ingress_acceptance_record))
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(_read_json(ns.verify_validator_handoff_ingress_certificate)) if ns.verify_validator_handoff_ingress_certificate else None
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet)) if ns.verify_validator_handoff_packet else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    report = verify_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.accepted_for_validator_adjudication else 1


def _run_validator_ingress_acceptance_record_summary_mode(ns: argparse.Namespace) -> int:
    record = SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(ns.verify_validator_ingress_acceptance_record))
    certificate = SemanticValidatorHandoffPacketIngressCertificate.model_validate(_read_json(ns.verify_validator_handoff_ingress_certificate)) if ns.verify_validator_handoff_ingress_certificate else None
    packet = SemanticValidatorHandoffPacket.model_validate(_read_json(ns.verify_validator_handoff_packet)) if ns.verify_validator_handoff_packet else None
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only)) if ns.verify_proposal_only else None
    summary = summarize_semantic_validator_ingress_acceptance_record(
        record,
        certificate=certificate,
        packet=packet,
        proposal=proposal,
        require_packet_evidence_on_proposal=not ns.allow_missing_packet_evidence_on_proposal,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "SUBMIT_ACCEPTED_SEMANTIC_PACKET_TO_VALIDATOR" else 1


def _run_validator_ingress_acceptance_ledger_mode(ns: argparse.Namespace) -> int:
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    ledger = build_semantic_validator_ingress_acceptance_ledger(records)
    payload = ledger.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if ledger.entry_count > 0 else 1


def _run_validator_ingress_acceptance_ledger_verification_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(_read_json(ns.verify_validator_ingress_acceptance_ledger))
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    report = verify_semantic_validator_ingress_acceptance_ledger(ledger, records=records or None)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.verified else 1


def _run_validator_ingress_acceptance_ledger_summary_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(_read_json(ns.verify_validator_ingress_acceptance_ledger))
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    summary = summarize_semantic_validator_ingress_acceptance_ledger(ledger, records=records or None)
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "SUBMIT_TERMINAL_ACCEPTED_PACKET_TO_VALIDATOR" else 1


def _run_validator_submission_packet_mode(ns: argparse.Namespace) -> int:
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(_read_json(ns.verify_validator_ingress_acceptance_ledger))
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    packet = build_semantic_validator_submission_packet(
        ledger,
        submitted_by=ns.submitted_by,
        submission_reason=ns.submission_reason,
        records=records or None,
    )
    payload = packet.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if packet.ready_for_validator_adjudication else 1


def _run_validator_submission_packet_verification_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorSubmissionPacket.model_validate(_read_json(ns.verify_validator_submission_packet))
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(_read_json(ns.verify_validator_ingress_acceptance_ledger)) if ns.verify_validator_ingress_acceptance_ledger else None
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    report = verify_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=records or None)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.ready_for_validator_adjudication else 1


def _run_validator_submission_packet_summary_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorSubmissionPacket.model_validate(_read_json(ns.verify_validator_submission_packet))
    ledger = SemanticValidatorIngressAcceptanceLedger.model_validate(_read_json(ns.verify_validator_ingress_acceptance_ledger)) if ns.verify_validator_ingress_acceptance_ledger else None
    records = [
        SemanticValidatorIngressAcceptanceRecord.model_validate(_read_json(path))
        for path in (ns.validator_ingress_acceptance_record or [])
    ]
    summary = summarize_semantic_validator_submission_packet(packet, acceptance_ledger=ledger, records=records or None)
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "SUBMIT_SEMANTIC_VALIDATOR_PACKET_TO_ADJUDICATION" else 1


def _run_validator_submission_packet_evidence_mode(ns: argparse.Namespace) -> int:
    packet = SemanticValidatorSubmissionPacket.model_validate(_read_json(ns.verify_validator_submission_packet))
    evidence = build_semantic_validator_submission_packet_evidence(packet)
    payload = evidence.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0


def _run_validator_submission_packet_evidence_verification_mode(ns: argparse.Namespace) -> int:
    evidence = Evidence.model_validate(_read_json(ns.verify_validator_submission_packet_evidence))
    packet = SemanticValidatorSubmissionPacket.model_validate(_read_json(ns.verify_validator_submission_packet)) if ns.verify_validator_submission_packet else None
    report = verify_semantic_validator_submission_packet_evidence(evidence, submission_packet=packet)
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.ready_for_validator_adjudication else 1


def _run_validator_submission_packet_evidence_summary_mode(ns: argparse.Namespace) -> int:
    evidence = Evidence.model_validate(_read_json(ns.verify_validator_submission_packet_evidence))
    packet = SemanticValidatorSubmissionPacket.model_validate(_read_json(ns.verify_validator_submission_packet)) if ns.verify_validator_submission_packet else None
    summary = summarize_semantic_validator_submission_packet_evidence(evidence, submission_packet=packet)
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "HAND_OFF_SUBMISSION_PACKET_EVIDENCE_TO_VALIDATOR" else 1


def _run_validator_submission_readiness_mode(ns: argparse.Namespace) -> int:
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only))
    evidence = Evidence.model_validate(_read_json(ns.verify_validator_submission_packet_evidence)) if ns.verify_validator_submission_packet_evidence else None
    report = build_semantic_validator_submission_readiness_report(
        proposal,
        submission_packet_evidence=evidence,
        require_submission_packet_evidence=not ns.allow_missing_submission_packet_evidence,
    )
    payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.ready_for_validator_adjudication else 1


def _run_validator_submission_readiness_summary_mode(ns: argparse.Namespace) -> int:
    proposal = ExperimentManifest.model_validate(_read_json(ns.verify_proposal_only))
    evidence = Evidence.model_validate(_read_json(ns.verify_validator_submission_packet_evidence)) if ns.verify_validator_submission_packet_evidence else None
    summary = summarize_semantic_validator_submission_readiness(
        proposal,
        submission_packet_evidence=evidence,
        require_submission_packet_evidence=not ns.allow_missing_submission_packet_evidence,
    )
    payload = summary.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, payload)
    sys.stdout.write(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if summary.recommended_action == "SUBMIT_PROPOSAL_TO_VALIDATOR_ADJUDICATION" else 1


__all__ = ['_run_validator_handoff_packet_mode', '_run_validator_handoff_packet_verification_mode', '_run_validator_handoff_packet_summary_mode', '_run_validator_handoff_packet_ingress_mode', '_run_validator_handoff_packet_ingress_summary_mode', '_run_validator_handoff_packet_ingress_certificate_mode', '_run_validator_handoff_packet_ingress_certificate_verification_mode', '_run_validator_handoff_packet_ingress_certificate_summary_mode', '_run_validator_ingress_acceptance_record_mode', '_run_validator_ingress_acceptance_record_verification_mode', '_run_validator_ingress_acceptance_record_summary_mode', '_run_validator_ingress_acceptance_ledger_mode', '_run_validator_ingress_acceptance_ledger_verification_mode', '_run_validator_ingress_acceptance_ledger_summary_mode', '_run_validator_submission_packet_mode', '_run_validator_submission_packet_verification_mode', '_run_validator_submission_packet_summary_mode', '_run_validator_submission_packet_evidence_mode', '_run_validator_submission_packet_evidence_verification_mode', '_run_validator_submission_packet_evidence_summary_mode', '_run_validator_submission_readiness_mode', '_run_validator_submission_readiness_summary_mode']
