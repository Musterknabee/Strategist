from __future__ import annotations

from strategy_validator.cli.research_preflight_common import _read_json, _write_json
from strategy_validator.cli.research_preflight_dispatch import dispatch_research_preflight
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
from strategy_validator.cli.research_preflight_parser import build_research_preflight_parser


def main(argv: list[str] | None = None) -> int:
    parser = build_research_preflight_parser()
    ns = parser.parse_args(argv)
    return dispatch_research_preflight(ns)


__all__ = [
    "main",
    "build_research_preflight_parser",
    "dispatch_research_preflight",
    "_read_json",
    "_write_json",
    '_run_integrity_mode', '_run_gate_artifact_verification_mode', '_run_handoff_artifact_verification_mode', '_run_bundle_verification_mode', '_run_bundle_manifest_verification_mode', '_run_bundle_release_preflight_mode', '_run_bundle_release_index_mode', '_run_bundle_release_index_verification_mode', '_run_release_capsule_mode', '_run_release_capsule_verification_mode', '_run_release_capsule_summary_mode', '_run_release_decision_record_mode', '_run_release_decision_record_verification_mode', '_run_release_decision_record_summary_mode', '_require_preflight_args', '_run_release_decision_ledger_mode', '_run_release_decision_ledger_verification_mode', '_run_release_decision_ledger_summary_mode', '_run_release_handoff_certificate_mode', '_run_release_handoff_certificate_verification_mode', '_run_release_handoff_certificate_summary_mode', '_run_release_handoff_certificate_evidence_mode', '_run_release_handoff_certificate_evidence_verification_mode', '_run_release_handoff_certificate_evidence_summary_mode', '_run_validator_handoff_packet_mode', '_run_validator_handoff_packet_verification_mode', '_run_validator_handoff_packet_summary_mode', '_run_validator_handoff_packet_ingress_mode', '_run_validator_handoff_packet_ingress_summary_mode', '_run_validator_handoff_packet_ingress_certificate_mode', '_run_validator_handoff_packet_ingress_certificate_verification_mode', '_run_validator_handoff_packet_ingress_certificate_summary_mode', '_run_validator_ingress_acceptance_record_mode', '_run_validator_ingress_acceptance_record_verification_mode', '_run_validator_ingress_acceptance_record_summary_mode', '_run_validator_ingress_acceptance_ledger_mode', '_run_validator_ingress_acceptance_ledger_verification_mode', '_run_validator_ingress_acceptance_ledger_summary_mode', '_run_validator_submission_packet_mode', '_run_validator_submission_packet_verification_mode', '_run_validator_submission_packet_summary_mode', '_run_validator_submission_packet_evidence_mode', '_run_validator_submission_packet_evidence_verification_mode', '_run_validator_submission_packet_evidence_summary_mode', '_run_validator_submission_readiness_mode', '_run_validator_submission_readiness_summary_mode',
]


if __name__ == "__main__":
    raise SystemExit(main())
