from __future__ import annotations

from datetime import datetime, timedelta

from strategy_validator.control_plane.operator_control_plane_bundle_stage_recurrence_surfaces import (
    build_operator_chronic_exit_certification_request,
    build_operator_chronic_exit_return_bridge_request,
    build_operator_chronic_instability_packet_request,
    build_operator_chronic_origin_restoration_audit_overlay_request,
    build_operator_chronic_origin_restoration_provenance_request,
    build_operator_chronic_remediation_mandate_ledger_request,
    build_operator_chronic_remediation_satisfaction_request,
    build_operator_chronic_watch_audit_convergence_request,
    build_operator_chronic_watch_handoff_request,
    build_operator_chronic_watch_outcome_request,
    build_operator_converged_normalization_attestation_request,
    build_operator_freeze_release_attestation_request,
    build_operator_freeze_release_gate_request,
    build_operator_monitored_rejoin_activation_request,
    build_operator_monitored_rejoin_normalization_bridge_request,
    build_operator_monitored_rejoin_policy_request,
    build_operator_normalization_bridge_activation_request,
    build_operator_provenance_aware_drift_policy_request,
    build_operator_recurrence_tribunal_disposition_request,
    build_operator_recurrence_tribunal_lane_request,
    materialize_operator_chronic_exit_certification,
    materialize_operator_chronic_exit_return_bridge,
    materialize_operator_chronic_instability_packet,
    materialize_operator_chronic_origin_restoration_audit_overlay,
    materialize_operator_chronic_origin_restoration_provenance,
    materialize_operator_chronic_remediation_mandate_ledger,
    materialize_operator_chronic_remediation_satisfaction,
    materialize_operator_chronic_watch_audit_convergence,
    materialize_operator_chronic_watch_handoff,
    materialize_operator_chronic_watch_outcome,
    materialize_operator_converged_normalization_attestation,
    materialize_operator_freeze_release_attestation,
    materialize_operator_freeze_release_gate,
    materialize_operator_monitored_rejoin_activation,
    materialize_operator_monitored_rejoin_normalization_bridge,
    materialize_operator_monitored_rejoin_policy,
    materialize_operator_normalization_bridge_activation,
    materialize_operator_provenance_aware_drift_policy,
    materialize_operator_recurrence_tribunal_disposition,
    materialize_operator_recurrence_tribunal_lane,
)

def materialize_operator_control_plane_bundle_recurrence_stage(request, *, emitted_at_utc: datetime, reopen_recurrence_policy, restoration_audit, chronic_instability_packet_request=None, recurrence_tribunal_lane_request=None, recurrence_tribunal_disposition_request=None, chronic_remediation_mandate_ledger_request=None, chronic_remediation_satisfaction_request=None, freeze_release_gate_request=None, freeze_release_attestation_request=None, chronic_exit_certification_request=None, chronic_exit_return_bridge_request=None, monitored_rejoin_policy_request=None, monitored_rejoin_activation_request=None, chronic_watch_handoff_request=None, chronic_watch_outcome_request=None, monitored_rejoin_normalization_bridge_request=None, normalization_bridge_activation_request=None, chronic_watch_audit_convergence_request=None, converged_normalization_attestation_request=None, chronic_origin_restoration_provenance_request=None, chronic_origin_restoration_audit_overlay_request=None, provenance_aware_drift_policy_request=None):
    chronic_instability_packet = materialize_operator_chronic_instability_packet(
        chronic_instability_packet_request or build_operator_chronic_instability_packet_request(
            packet_root=request.bundle_root / 'chronic_instability_packet',
            board_label=request.board_label,
            emitted_at_utc=emitted_at_utc,
        ),
        reopen_recurrence_policy=reopen_recurrence_policy,
        board_label=request.board_label,
    )
    recurrence_tribunal_lane = materialize_operator_recurrence_tribunal_lane(
        recurrence_tribunal_lane_request or build_operator_recurrence_tribunal_lane_request(
            tribunal_root=request.bundle_root / 'recurrence_tribunal_lane',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        chronic_instability_packet=chronic_instability_packet,
        board_label=request.board_label,
    )
    recurrence_tribunal_disposition = materialize_operator_recurrence_tribunal_disposition(
        recurrence_tribunal_disposition_request or build_operator_recurrence_tribunal_disposition_request(
            disposition_root=request.bundle_root / 'recurrence_tribunal_disposition',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        recurrence_tribunal_lane=recurrence_tribunal_lane,
        board_label=request.board_label,
    )
    chronic_remediation_mandate_ledger = materialize_operator_chronic_remediation_mandate_ledger(
        chronic_remediation_mandate_ledger_request or build_operator_chronic_remediation_mandate_ledger_request(
            ledger_root=request.bundle_root / 'chronic_remediation_mandate_ledger',
            board_label=request.board_label,
            mandated_at_utc=emitted_at_utc,
        ),
        recurrence_tribunal_disposition=recurrence_tribunal_disposition,
        board_label=request.board_label,
    )
    chronic_remediation_satisfaction = materialize_operator_chronic_remediation_satisfaction(
        chronic_remediation_satisfaction_request or build_operator_chronic_remediation_satisfaction_request(
            satisfaction_root=request.bundle_root / 'chronic_remediation_satisfaction',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_remediation_mandate_ledger=chronic_remediation_mandate_ledger,
        board_label=request.board_label,
    )
    freeze_release_gate = materialize_operator_freeze_release_gate(
        freeze_release_gate_request or build_operator_freeze_release_gate_request(
            gate_root=request.bundle_root / 'freeze_release_gate',
            board_label=request.board_label,
            reviewed_at_utc=emitted_at_utc,
        ),
        chronic_remediation_satisfaction=chronic_remediation_satisfaction,
        board_label=request.board_label,
    )
    freeze_release_attestation = materialize_operator_freeze_release_attestation(
        freeze_release_attestation_request or build_operator_freeze_release_attestation_request(
            attestation_root=request.bundle_root / 'freeze_release_attestation',
            board_label=request.board_label,
            attested_at_utc=emitted_at_utc,
        ),
        freeze_release_gate=freeze_release_gate,
        board_label=request.board_label,
    )
    chronic_exit_certification = materialize_operator_chronic_exit_certification(
        chronic_exit_certification_request or build_operator_chronic_exit_certification_request(
            certification_root=request.bundle_root / 'chronic_exit_certification',
            board_label=request.board_label,
            certified_at_utc=emitted_at_utc,
        ),
        freeze_release_attestation=freeze_release_attestation,
        board_label=request.board_label,
    )
    chronic_exit_return_bridge = materialize_operator_chronic_exit_return_bridge(
        chronic_exit_return_bridge_request or build_operator_chronic_exit_return_bridge_request(
            bridge_root=request.bundle_root / 'chronic_exit_return_bridge',
            board_label=request.board_label,
            bridged_at_utc=emitted_at_utc,
        ),
        chronic_exit_certification=chronic_exit_certification,
        board_label=request.board_label,
    )
    monitored_rejoin_policy = materialize_operator_monitored_rejoin_policy(
        monitored_rejoin_policy_request or build_operator_monitored_rejoin_policy_request(
            policy_root=request.bundle_root / 'monitored_rejoin_policy',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_exit_return_bridge=chronic_exit_return_bridge,
        board_label=request.board_label,
    )
    monitored_rejoin_activation = materialize_operator_monitored_rejoin_activation(
        monitored_rejoin_activation_request or build_operator_monitored_rejoin_activation_request(
            activation_root=request.bundle_root / 'monitored_rejoin_activation',
            board_label=request.board_label,
            activator_label='chronic-rejoin-activator',
            activated_at_utc=emitted_at_utc,
        ),
        monitored_rejoin_policy=monitored_rejoin_policy,
        board_label=request.board_label,
    )
    chronic_watch_handoff = materialize_operator_chronic_watch_handoff(
        chronic_watch_handoff_request or build_operator_chronic_watch_handoff_request(
            handoff_root=request.bundle_root / 'chronic_watch_handoff',
            board_label=request.board_label,
            handoff_label='chronic-watch-handoff',
            handed_off_at_utc=emitted_at_utc - timedelta(days=2),
        ),
        monitored_rejoin_activation=monitored_rejoin_activation,
        board_label=request.board_label,
    )
    chronic_watch_outcome = materialize_operator_chronic_watch_outcome(
        chronic_watch_outcome_request or build_operator_chronic_watch_outcome_request(
            outcome_root=request.bundle_root / 'chronic_watch_outcome',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_watch_handoff=chronic_watch_handoff,
        board_label=request.board_label,
    )
    monitored_rejoin_normalization_bridge = materialize_operator_monitored_rejoin_normalization_bridge(
        monitored_rejoin_normalization_bridge_request or build_operator_monitored_rejoin_normalization_bridge_request(
            bridge_root=request.bundle_root / 'monitored_rejoin_normalization_bridge',
            board_label=request.board_label,
            bridged_at_utc=emitted_at_utc,
        ),
        chronic_watch_outcome=chronic_watch_outcome,
        board_label=request.board_label,
    )
    normalization_bridge_activation = materialize_operator_normalization_bridge_activation(
        normalization_bridge_activation_request or build_operator_normalization_bridge_activation_request(
            activation_root=request.bundle_root / 'normalization_bridge_activation',
            board_label=request.board_label,
            activated_at_utc=emitted_at_utc,
            monitoring_started_at_utc=emitted_at_utc - timedelta(hours=2),
        ),
        monitored_rejoin_normalization_bridge=monitored_rejoin_normalization_bridge,
        board_label=request.board_label,
    )
    chronic_watch_audit_convergence = materialize_operator_chronic_watch_audit_convergence(
        chronic_watch_audit_convergence_request or build_operator_chronic_watch_audit_convergence_request(
            convergence_root=request.bundle_root / 'chronic_watch_audit_convergence',
            board_label=request.board_label,
            converged_at_utc=emitted_at_utc,
        ),
        normalization_bridge_activation=normalization_bridge_activation,
        board_label=request.board_label,
    )
    converged_normalization_attestation = materialize_operator_converged_normalization_attestation(
        converged_normalization_attestation_request or build_operator_converged_normalization_attestation_request(
            attestation_root=request.bundle_root / 'converged_normalization_attestation',
            board_label=request.board_label,
            attested_at_utc=emitted_at_utc,
        ),
        chronic_watch_audit_convergence=chronic_watch_audit_convergence,
        board_label=request.board_label,
    )
    chronic_origin_restoration_provenance = materialize_operator_chronic_origin_restoration_provenance(
        chronic_origin_restoration_provenance_request or build_operator_chronic_origin_restoration_provenance_request(
            provenance_root=request.bundle_root / 'chronic_origin_restoration_provenance',
            board_label=request.board_label,
            recorded_at_utc=emitted_at_utc,
        ),
        converged_normalization_attestation=converged_normalization_attestation,
        board_label=request.board_label,
    )
    chronic_origin_restoration_audit_overlay = materialize_operator_chronic_origin_restoration_audit_overlay(
        chronic_origin_restoration_audit_overlay_request or build_operator_chronic_origin_restoration_audit_overlay_request(
            overlay_root=request.bundle_root / 'chronic_origin_restoration_audit_overlay',
            board_label=request.board_label,
            overlaid_at_utc=emitted_at_utc,
        ),
        chronic_origin_restoration_provenance=chronic_origin_restoration_provenance,
        restoration_audit=restoration_audit,
        board_label=request.board_label,
    )
    provenance_aware_drift_policy = materialize_operator_provenance_aware_drift_policy(
        provenance_aware_drift_policy_request or build_operator_provenance_aware_drift_policy_request(
            policy_root=request.bundle_root / 'provenance_aware_drift_policy',
            board_label=request.board_label,
            evaluated_at_utc=emitted_at_utc,
        ),
        chronic_origin_restoration_audit_overlay=chronic_origin_restoration_audit_overlay,
        board_label=request.board_label,
    )
    return {
        'chronic_instability_packet': chronic_instability_packet,
        'recurrence_tribunal_lane': recurrence_tribunal_lane,
        'recurrence_tribunal_disposition': recurrence_tribunal_disposition,
        'chronic_remediation_mandate_ledger': chronic_remediation_mandate_ledger,
        'chronic_remediation_satisfaction': chronic_remediation_satisfaction,
        'freeze_release_gate': freeze_release_gate,
        'freeze_release_attestation': freeze_release_attestation,
        'chronic_exit_certification': chronic_exit_certification,
        'chronic_exit_return_bridge': chronic_exit_return_bridge,
        'monitored_rejoin_policy': monitored_rejoin_policy,
        'monitored_rejoin_activation': monitored_rejoin_activation,
        'chronic_watch_handoff': chronic_watch_handoff,
        'chronic_watch_outcome': chronic_watch_outcome,
        'monitored_rejoin_normalization_bridge': monitored_rejoin_normalization_bridge,
        'normalization_bridge_activation': normalization_bridge_activation,
        'chronic_watch_audit_convergence': chronic_watch_audit_convergence,
        'converged_normalization_attestation': converged_normalization_attestation,
        'chronic_origin_restoration_provenance': chronic_origin_restoration_provenance,
        'chronic_origin_restoration_audit_overlay': chronic_origin_restoration_audit_overlay,
        'provenance_aware_drift_policy': provenance_aware_drift_policy,
    }


__all__ = ['materialize_operator_control_plane_bundle_recurrence_stage']
