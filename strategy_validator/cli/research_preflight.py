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


def _read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _write_json(path: str | Path, payload: dict[str, Any]) -> None:
    Path(path).write_text(json.dumps(payload, indent=2, sort_keys=True, allow_nan=True) + "\n", encoding="utf-8")


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


def main(argv: list[str] | None = None) -> int:
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
    ns = parser.parse_args(argv)


    if ns.validator_submission_packet_json:
        if not ns.verify_validator_ingress_acceptance_ledger:
            raise SystemExit("--validator-submission-packet-json requires --verify-validator-ingress-acceptance-ledger")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--validator-submission-packet-json cannot be combined with preflight materialization or handoff-generation arguments")
        return _run_validator_submission_packet_mode(ns)

    if ns.verify_proposal_only and (ns.validator_submission_readiness_json or ns.validator_submission_readiness_summary_json):
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--validator-submission-readiness-json cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_submission_readiness_summary_json:
            return _run_validator_submission_readiness_summary_mode(ns)
        return _run_validator_submission_readiness_mode(ns)

    if ns.verify_validator_submission_packet_evidence:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-submission-packet-evidence cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_submission_packet_evidence_summary_json:
            return _run_validator_submission_packet_evidence_summary_mode(ns)
        return _run_validator_submission_packet_evidence_verification_mode(ns)

    if ns.verify_validator_submission_packet:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-submission-packet cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_submission_packet_evidence_json:
            return _run_validator_submission_packet_evidence_mode(ns)
        if ns.validator_submission_packet_summary_json:
            return _run_validator_submission_packet_summary_mode(ns)
        return _run_validator_submission_packet_verification_mode(ns)


    if ns.validator_ingress_acceptance_ledger_json:
        if not ns.validator_ingress_acceptance_record:
            raise SystemExit("--validator-ingress-acceptance-ledger-json requires at least one --validator-ingress-acceptance-record")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--validator-ingress-acceptance-ledger-json cannot be combined with preflight materialization or handoff-generation arguments")
        return _run_validator_ingress_acceptance_ledger_mode(ns)

    if ns.verify_validator_ingress_acceptance_ledger:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-ingress-acceptance-ledger cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_ingress_acceptance_ledger_summary_json:
            return _run_validator_ingress_acceptance_ledger_summary_mode(ns)
        return _run_validator_ingress_acceptance_ledger_verification_mode(ns)


    if ns.verify_validator_ingress_acceptance_record:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-ingress-acceptance-record cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_ingress_acceptance_record_summary_json:
            return _run_validator_ingress_acceptance_record_summary_mode(ns)
        return _run_validator_ingress_acceptance_record_verification_mode(ns)


    if ns.verify_validator_handoff_ingress_certificate:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-handoff-ingress-certificate cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_ingress_acceptance_record_json:
            return _run_validator_ingress_acceptance_record_mode(ns)
        if ns.validator_handoff_ingress_certificate_summary_json:
            return _run_validator_handoff_packet_ingress_certificate_summary_mode(ns)
        return _run_validator_handoff_packet_ingress_certificate_verification_mode(ns)

    if ns.verify_validator_handoff_packet:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-validator-handoff-packet cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_handoff_ingress_certificate_json:
            return _run_validator_handoff_packet_ingress_certificate_mode(ns)
        if ns.validator_handoff_packet_ingress_summary_json:
            return _run_validator_handoff_packet_ingress_summary_mode(ns)
        if ns.validator_handoff_packet_ingress_json:
            return _run_validator_handoff_packet_ingress_mode(ns)
        if ns.validator_handoff_packet_summary_json:
            return _run_validator_handoff_packet_summary_mode(ns)
        return _run_validator_handoff_packet_verification_mode(ns)

    if ns.verify_release_handoff_certificate_evidence:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-release-handoff-certificate-evidence cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.validator_handoff_packet_json:
            return _run_validator_handoff_packet_mode(ns)
        if ns.release_handoff_certificate_evidence_summary_json:
            return _run_release_handoff_certificate_evidence_summary_mode(ns)
        return _run_release_handoff_certificate_evidence_verification_mode(ns)

    if ns.verify_release_handoff_certificate:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-release-handoff-certificate cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.release_handoff_certificate_summary_json:
            return _run_release_handoff_certificate_summary_mode(ns)
        if ns.release_handoff_certificate_evidence_json:
            return _run_release_handoff_certificate_evidence_mode(ns)
        return _run_release_handoff_certificate_verification_mode(ns)

    if ns.release_handoff_certificate_json:
        if not ns.verify_release_decision_ledger:
            raise SystemExit("--release-handoff-certificate-json requires --verify-release-decision-ledger")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--release-handoff-certificate-json cannot be combined with preflight materialization or handoff-generation arguments")
        return _run_release_handoff_certificate_mode(ns)

    if ns.release_decision_ledger_json:
        if not ns.release_decision_record:
            raise SystemExit("--release-decision-ledger-json requires at least one --release-decision-record")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--release-decision-ledger-json cannot be combined with preflight materialization or handoff-generation arguments")
        return _run_release_decision_ledger_mode(ns)

    if ns.verify_release_decision_ledger:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-release-decision-ledger cannot be combined with preflight materialization or handoff-generation arguments")
        if ns.release_handoff_certificate_json:
            return _run_release_handoff_certificate_mode(ns)
        if ns.release_decision_ledger_summary_json:
            return _run_release_decision_ledger_summary_mode(ns)
        return _run_release_decision_ledger_verification_mode(ns)

    if ns.verify_release_decision_record:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact, ns.release_capsule_json, ns.release_capsule_summary_json, ns.release_decision_record_json]):
            raise SystemExit("--verify-release-decision-record cannot be combined with generation or materialization arguments")
        if ns.release_decision_record_summary_json:
            return _run_release_decision_record_summary_mode(ns)
        return _run_release_decision_record_verification_mode(ns)

    if ns.release_decision_record_json:
        if not ns.verify_release_capsule:
            raise SystemExit("--release-decision-record-json requires --verify-release-capsule")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact, ns.release_capsule_json, ns.release_capsule_summary_json]):
            raise SystemExit("--release-decision-record-json cannot be combined with other capsule generation/summary modes")
        return _run_release_decision_record_mode(ns)


    if ns.verify_release_capsule:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-release-capsule cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_preflight_json, ns.bundle_release_index_json, ns.release_capsule_json, ns.release_decision_record_json, ns.release_decision_record_summary_json]):
            raise SystemExit("--verify-release-capsule cannot be combined with other summary/artifact emission modes")
        if ns.release_capsule_summary_json:
            return _run_release_capsule_summary_mode(ns)
        return _run_release_capsule_verification_mode(ns)

    if ns.release_capsule_json:
        if not ns.verify_bundle_release_index:
            raise SystemExit("--release-capsule-json requires --verify-bundle-release-index")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--release-capsule-json cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_preflight_json, ns.bundle_release_index_json]):
            raise SystemExit("--release-capsule-json cannot be combined with other summary/artifact emission modes")
        return _run_release_capsule_mode(ns)
    if ns.verify_bundle_release_index:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-bundle-release-index cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_preflight_json, ns.bundle_release_index_json, ns.release_capsule_json, ns.release_capsule_summary_json, ns.release_decision_record_json, ns.release_decision_record_summary_json]):
            raise SystemExit("--verify-bundle-release-index cannot be combined with other summary/artifact emission modes")
        return _run_bundle_release_index_verification_mode(ns)

    if ns.bundle_release_index_json:
        if not ns.verify_bundle:
            raise SystemExit("--bundle-release-index-json requires --verify-bundle")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--bundle-release-index-json cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_preflight_json]):
            raise SystemExit("--bundle-release-index-json cannot be combined with other summary/artifact emission modes")
        return _run_bundle_release_index_mode(ns)

    if ns.bundle_release_preflight_json:
        if not ns.verify_bundle:
            raise SystemExit("--bundle-release-preflight-json requires --verify-bundle")
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--bundle-release-preflight-json cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_index_json, ns.release_capsule_json, ns.release_capsule_summary_json, ns.release_decision_record_json, ns.release_decision_record_summary_json]):
            raise SystemExit("--bundle-release-preflight-json cannot be combined with other summary/artifact emission modes")
        return _run_bundle_release_preflight_mode(ns)

    if ns.verify_bundle_manifest:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-bundle-manifest cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json, ns.bundle_summary_json, ns.bundle_manifest_json, ns.bundle_release_index_json, ns.release_capsule_json, ns.release_capsule_summary_json, ns.release_decision_record_json, ns.release_decision_record_summary_json]):
            raise SystemExit("--verify-bundle-manifest cannot be combined with summary/artifact/readiness emission modes")
        return _run_bundle_manifest_verification_mode(ns)

    if ns.verify_bundle:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-bundle cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json]):
            raise SystemExit("--verify-bundle cannot be combined with integrity/readiness emission modes")
        return _run_bundle_verification_mode(ns)

    if ns.verify_handoff_artifact:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal, ns.gate_artifact, ns.handoff_artifact, ns.require_gate_artifact]):
            raise SystemExit("--verify-handoff-artifact cannot be combined with preflight materialization or handoff-generation arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json]):
            raise SystemExit("--verify-handoff-artifact cannot be combined with summary/artifact/readiness emission modes")
        return _run_handoff_artifact_verification_mode(ns)

    if ns.verify_gate_artifact:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal]):
            raise SystemExit("--verify-gate-artifact cannot be combined with preflight materialization arguments")
        if any([ns.verify_summary_json, ns.adjudication_gate_summary_json, ns.adjudication_gate_artifact_json, ns.adjudication_readiness_json, ns.adjudication_handoff_artifact_json, ns.adjudication_bundle_json]):
            raise SystemExit("--verify-gate-artifact cannot be combined with summary/artifact/readiness emission modes")
        return _run_gate_artifact_verification_mode(ns)

    if ns.verify_proposal_only:
        if any([ns.artifact, ns.published_at, ns.available_at, ns.write_updated_proposal]):
            raise SystemExit("--verify-proposal-only cannot be combined with preflight materialization arguments")
        return _run_integrity_mode(ns)

    if ns.validator_submission_readiness_json:
        raise SystemExit("--validator-submission-readiness-json requires --verify-proposal-only")
    if ns.validator_submission_readiness_summary_json:
        raise SystemExit("--validator-submission-readiness-summary-json requires --verify-proposal-only")
    if ns.release_handoff_certificate_evidence_json:
        raise SystemExit("--release-handoff-certificate-evidence-json requires --verify-release-handoff-certificate")
    if ns.release_handoff_certificate_evidence_summary_json:
        raise SystemExit("--release-handoff-certificate-evidence-summary-json requires --verify-release-handoff-certificate-evidence")
    if ns.validator_handoff_packet_json:
        raise SystemExit("--validator-handoff-packet-json requires --verify-release-handoff-certificate-evidence")
    if ns.validator_handoff_packet_summary_json:
        raise SystemExit("--validator-handoff-packet-summary-json requires --verify-validator-handoff-packet")
    if ns.validator_handoff_packet_ingress_json:
        raise SystemExit("--validator-handoff-packet-ingress-json requires --verify-validator-handoff-packet")
    if ns.validator_handoff_packet_ingress_summary_json:
        raise SystemExit("--validator-handoff-packet-ingress-summary-json requires --verify-validator-handoff-packet")
    if ns.validator_handoff_ingress_certificate_json:
        raise SystemExit("--validator-handoff-ingress-certificate-json requires --verify-validator-handoff-packet")
    if ns.validator_handoff_ingress_certificate_summary_json:
        raise SystemExit("--validator-handoff-ingress-certificate-summary-json requires --verify-validator-handoff-ingress-certificate")
    if ns.validator_ingress_acceptance_record_json:
        raise SystemExit("--validator-ingress-acceptance-record-json requires --verify-validator-handoff-ingress-certificate")
    if ns.validator_ingress_acceptance_record_summary_json:
        raise SystemExit("--validator-ingress-acceptance-record-summary-json requires --verify-validator-ingress-acceptance-record")
    if ns.validator_ingress_acceptance_ledger_json:
        raise SystemExit("--validator-ingress-acceptance-ledger-json requires --validator-ingress-acceptance-record")
    if ns.validator_ingress_acceptance_ledger_summary_json:
        raise SystemExit("--validator-ingress-acceptance-ledger-summary-json requires --verify-validator-ingress-acceptance-ledger")
    if ns.release_decision_record_summary_json:
        raise SystemExit("--release-decision-record-summary-json requires --verify-release-decision-record")
    if ns.verify_summary_json:
        raise SystemExit("--verify-summary-json requires --verify-proposal-only")
    if ns.adjudication_gate_summary_json:
        raise SystemExit("--adjudication-gate-summary-json requires --verify-proposal-only")
    if ns.adjudication_gate_artifact_json:
        raise SystemExit("--adjudication-gate-artifact-json requires --verify-proposal-only")
    if ns.adjudication_readiness_json:
        raise SystemExit("--adjudication-readiness-json requires --verify-proposal-only")
    if ns.adjudication_handoff_artifact_json:
        raise SystemExit("--adjudication-handoff-artifact-json requires --verify-proposal-only")
    if ns.adjudication_bundle_json:
        raise SystemExit("--adjudication-bundle-json requires --verify-proposal-only")
    if ns.bundle_summary_json:
        raise SystemExit("--bundle-summary-json requires --verify-bundle")
    if ns.bundle_manifest_json:
        raise SystemExit("--bundle-manifest-json requires --verify-bundle")
    if ns.gate_artifact or ns.handoff_artifact or ns.require_gate_artifact:
        raise SystemExit("--gate-artifact/--handoff-artifact/--require-gate-artifact require --verify-proposal-only with --adjudication-readiness-json, --adjudication-handoff-artifact-json, or --adjudication-bundle-json")

    _require_preflight_args(ns)
    proposal = ExperimentManifest.model_validate(_read_json(ns.proposal))
    artifact = FeatureFactoryArtifact.model_validate(_read_json(ns.artifact))
    report = run_semantic_research_preflight(
        proposal,
        artifact,
        published_at=ns.published_at,
        available_at=ns.available_at,
        asset_id=ns.asset_id,
        dataset_id=ns.dataset_id,
        attach_to_proposal=not ns.dry_run,
    )

    if ns.write_updated_proposal:
        if ns.dry_run:
            raise SystemExit("--write-updated-proposal cannot be combined with --dry-run")
        _write_json(ns.write_updated_proposal, proposal.model_dump(mode="json"))

    report_payload = report.model_dump(mode="json")
    if ns.write_report:
        _write_json(ns.write_report, report_payload)

    sys.stdout.write(json.dumps(report_payload, indent=2, sort_keys=True, allow_nan=True) + "\n")
    sys.stdout.flush()
    return 0 if report.evidence_verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
