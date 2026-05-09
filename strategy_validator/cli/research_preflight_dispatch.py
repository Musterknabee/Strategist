from __future__ import annotations

import argparse
import json
import sys

from strategy_validator.application.research_preflight import run_semantic_research_preflight
from strategy_validator.cli.research_preflight_common import _read_json, _write_json
from strategy_validator.cli.research_preflight_modes import (
    _run_integrity_mode,
    _run_gate_artifact_verification_mode,
    _run_handoff_artifact_verification_mode,
    _run_bundle_verification_mode,
    _run_bundle_manifest_verification_mode,
    _run_bundle_release_preflight_mode,
    _run_bundle_release_index_mode,
    _run_bundle_release_index_verification_mode,
    _run_release_capsule_mode,
    _run_release_capsule_verification_mode,
    _run_release_capsule_summary_mode,
    _run_release_decision_record_mode,
    _run_release_decision_record_verification_mode,
    _run_release_decision_record_summary_mode,
    _require_preflight_args,
    _run_release_decision_ledger_mode,
    _run_release_decision_ledger_verification_mode,
    _run_release_decision_ledger_summary_mode,
    _run_release_handoff_certificate_mode,
    _run_release_handoff_certificate_verification_mode,
    _run_release_handoff_certificate_summary_mode,
    _run_release_handoff_certificate_evidence_mode,
    _run_release_handoff_certificate_evidence_verification_mode,
    _run_release_handoff_certificate_evidence_summary_mode,
    _run_validator_handoff_packet_mode,
    _run_validator_handoff_packet_verification_mode,
    _run_validator_handoff_packet_summary_mode,
    _run_validator_handoff_packet_ingress_mode,
    _run_validator_handoff_packet_ingress_summary_mode,
    _run_validator_handoff_packet_ingress_certificate_mode,
    _run_validator_handoff_packet_ingress_certificate_verification_mode,
    _run_validator_handoff_packet_ingress_certificate_summary_mode,
    _run_validator_ingress_acceptance_record_mode,
    _run_validator_ingress_acceptance_record_verification_mode,
    _run_validator_ingress_acceptance_record_summary_mode,
    _run_validator_ingress_acceptance_ledger_mode,
    _run_validator_ingress_acceptance_ledger_verification_mode,
    _run_validator_ingress_acceptance_ledger_summary_mode,
    _run_validator_submission_packet_mode,
    _run_validator_submission_packet_verification_mode,
    _run_validator_submission_packet_summary_mode,
    _run_validator_submission_packet_evidence_mode,
    _run_validator_submission_packet_evidence_verification_mode,
    _run_validator_submission_packet_evidence_summary_mode,
    _run_validator_submission_readiness_mode,
    _run_validator_submission_readiness_summary_mode,
)
from strategy_validator.contracts.experiments import ExperimentManifest
from strategy_validator.contracts.semantic import FeatureFactoryArtifact


def dispatch_research_preflight(ns: argparse.Namespace) -> int:


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


__all__ = ["dispatch_research_preflight"]
