from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_strategy_reporting_commands import register_oracle_strategy_reporting_commands
from strategy_validator.cli.oracle_strategy_reporting_runners import (
    cmd_oracle_advisory,
    cmd_oracle_contradiction_resolution,
    cmd_oracle_doctrine_adaptation,
    cmd_oracle_evidence,
    cmd_oracle_opportunity_queue,
    cmd_oracle_regime_transition_signal,
    cmd_oracle_research_execution_memory,
    cmd_oracle_research_planner,
    cmd_oracle_scenario_lab,
    cmd_oracle_sensor_ingest,
    cmd_oracle_signal_fusion,
    cmd_oracle_strategic_artifact_evidence,
    cmd_oracle_strategic_briefing,
    cmd_oracle_strategic_campaign,
    cmd_oracle_strategic_campaign_execution,
    cmd_oracle_strategic_intervention,
    cmd_oracle_strategic_memory_horizon,
    cmd_oracle_strategic_narrative,
    cmd_oracle_strategic_stack_evidence,
    cmd_oracle_strategic_tension,
    cmd_oracle_strategy_cohort,
    cmd_oracle_strategy_health_posterior,
    cmd_oracle_thesis_graph,
    cmd_oracle_thesis_memory,
    cmd_verify_oracle_evidence,
    cmd_verify_oracle_strategic_artifact_evidence,
    cmd_verify_oracle_strategic_stack_evidence,
)

STRATEGY_RUNNERS = {
    "cmd_oracle_advisory": cmd_oracle_advisory,
    "cmd_oracle_sensor_ingest": cmd_oracle_sensor_ingest,
    "cmd_oracle_signal_fusion": cmd_oracle_signal_fusion,
    "cmd_oracle_opportunity_queue": cmd_oracle_opportunity_queue,
    "cmd_oracle_strategy_health_posterior": cmd_oracle_strategy_health_posterior,
    "cmd_oracle_regime_transition_signal": cmd_oracle_regime_transition_signal,
    "cmd_oracle_thesis_memory": cmd_oracle_thesis_memory,
    "cmd_oracle_strategic_briefing": cmd_oracle_strategic_briefing,
    "cmd_oracle_strategic_stack_evidence": cmd_oracle_strategic_stack_evidence,
    "cmd_verify_oracle_strategic_stack_evidence": cmd_verify_oracle_strategic_stack_evidence,
    "cmd_oracle_strategic_artifact_evidence": cmd_oracle_strategic_artifact_evidence,
    "cmd_verify_oracle_strategic_artifact_evidence": cmd_verify_oracle_strategic_artifact_evidence,
    "cmd_oracle_evidence": cmd_oracle_evidence,
    "cmd_verify_oracle_evidence": cmd_verify_oracle_evidence,
    "cmd_oracle_strategic_memory_horizon": cmd_oracle_strategic_memory_horizon,
    "cmd_oracle_contradiction_resolution": cmd_oracle_contradiction_resolution,
    "cmd_oracle_strategic_intervention": cmd_oracle_strategic_intervention,
    "cmd_oracle_strategic_campaign_execution": cmd_oracle_strategic_campaign_execution,
    "cmd_oracle_strategic_campaign": cmd_oracle_strategic_campaign,
    "cmd_oracle_scenario_lab": cmd_oracle_scenario_lab,
    "cmd_oracle_strategy_cohort": cmd_oracle_strategy_cohort,
    "cmd_oracle_doctrine_adaptation": cmd_oracle_doctrine_adaptation,
    "cmd_oracle_research_planner": cmd_oracle_research_planner,
    "cmd_oracle_research_execution_memory": cmd_oracle_research_execution_memory,
    "cmd_oracle_thesis_graph": cmd_oracle_thesis_graph,
    "cmd_oracle_strategic_narrative": cmd_oracle_strategic_narrative,
    "cmd_oracle_strategic_tension": cmd_oracle_strategic_tension,
}


def register_oracle_strategy_runtime_commands(
    sub: argparse._SubParsersAction[argparse.ArgumentParser],
) -> None:
    register_oracle_strategy_reporting_commands(sub, runners=STRATEGY_RUNNERS)
