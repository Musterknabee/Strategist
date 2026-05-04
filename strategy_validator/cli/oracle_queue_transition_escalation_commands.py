from __future__ import annotations

import argparse

from strategy_validator.cli.command_registry import CommandSpec, register_commands
from strategy_validator.cli.oracle_queue_command_configs import (
    _configure_oracle_operator_control_plane_bundle,
    _configure_oracle_operator_decision_execution,
    _configure_oracle_operator_decision_journal,
    _configure_oracle_operator_escalation_closure,
    _configure_oracle_operator_escalation_packet,
    _configure_oracle_operator_escalation_routing,
    _configure_oracle_operator_escalation_sla,
    _configure_oracle_operator_supervisor_review,
)


def register_oracle_queue_transition_escalation_commands(
    subparsers: argparse._SubParsersAction[argparse.ArgumentParser],
    *,
    runners: dict[str, object],
) -> None:
    register_commands(
        subparsers,
        [
            CommandSpec('oracle-operator-decision-journal', 'Materialize an append-safe replayable operator decision journal over workboard action contracts', _configure_oracle_operator_decision_journal, runners['oracle-operator-decision-journal']),
            CommandSpec('oracle-operator-decision-execution', 'Materialize a policy-governed execution report for operator workboard actions', _configure_oracle_operator_decision_execution, runners['oracle-operator-decision-execution']),
            CommandSpec('oracle-operator-escalation-routing', 'Materialize typed escalation routing destinations and remediation obligations for governed executions', _configure_oracle_operator_escalation_routing, runners['oracle-operator-escalation-routing']),
            CommandSpec('oracle-operator-escalation-packet', 'Materialize supervisor-ready escalation packets for routed escalations', _configure_oracle_operator_escalation_packet, runners['oracle-operator-escalation-packet']),
            CommandSpec('oracle-operator-escalation-sla', 'Materialize escalation SLA, aging, and breach posture for supervisor review packets', _configure_oracle_operator_escalation_sla, runners['oracle-operator-escalation-sla']),
            CommandSpec('oracle-operator-supervisor-review', 'Materialize supervisor dispositions for escalated packets', _configure_oracle_operator_supervisor_review, runners['oracle-operator-supervisor-review']),
            CommandSpec('oracle-operator-escalation-closure', 'Materialize escalation closure, requeue, or open-loop status from supervisor review', _configure_oracle_operator_escalation_closure, runners['oracle-operator-escalation-closure']),
            CommandSpec('oracle-operator-control-plane-bundle', 'Materialize a full operator control-plane bundle over governance, escalation, reentry, recurrence, and remediation state', _configure_oracle_operator_control_plane_bundle, runners['oracle-operator-control-plane-bundle']),
        ],
    )


__all__ = ['register_oracle_queue_transition_escalation_commands']
