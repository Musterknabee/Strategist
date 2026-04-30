"""Bounded runtime registration for operator queue escalation/review/closure commands."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_queue_commands import (
    cmd_oracle_operator_control_plane_bundle,
    cmd_oracle_operator_decision_execution,
    cmd_oracle_operator_decision_journal,
    cmd_oracle_operator_escalation_closure,
    cmd_oracle_operator_escalation_packet,
    cmd_oracle_operator_escalation_routing,
    cmd_oracle_operator_escalation_sla,
    cmd_oracle_operator_supervisor_review,
)
from strategy_validator.cli.oracle_queue_transition_escalation_commands import register_oracle_queue_transition_escalation_commands

OPERATOR_QUEUE_TRANSITION_ESCALATION_RUNNERS = {
    "oracle-operator-decision-journal": cmd_oracle_operator_decision_journal,
    "oracle-operator-decision-execution": cmd_oracle_operator_decision_execution,
    "oracle-operator-escalation-routing": cmd_oracle_operator_escalation_routing,
    "oracle-operator-escalation-packet": cmd_oracle_operator_escalation_packet,
    "oracle-operator-escalation-sla": cmd_oracle_operator_escalation_sla,
    "oracle-operator-supervisor-review": cmd_oracle_operator_supervisor_review,
    "oracle-operator-escalation-closure": cmd_oracle_operator_escalation_closure,
    "oracle-operator-control-plane-bundle": cmd_oracle_operator_control_plane_bundle,
}


def register_oracle_operator_queue_transition_escalation_runtime_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    """Register bounded operator queue escalation/review/closure runtime commands."""
    register_oracle_queue_transition_escalation_commands(sub, runners=OPERATOR_QUEUE_TRANSITION_ESCALATION_RUNNERS)
