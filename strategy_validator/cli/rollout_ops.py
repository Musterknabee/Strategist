"""Controlled rollout operations CLI dispatcher."""
from __future__ import annotations

import argparse

from strategy_validator.cli.oracle_projection_commands import cmd_oracle_projection_artifact_query, register_oracle_projection_commands
from strategy_validator.cli.rollout_closure_commands import register_rollout_closure_commands
from strategy_validator.cli.oracle_event_constitutional_commands import register_oracle_event_constitutional_commands
from strategy_validator.cli.oracle_briefing_replay_commands import register_oracle_briefing_replay_commands
from strategy_validator.cli.oracle_strategy_reporting_commands import register_oracle_strategy_reporting_commands
from strategy_validator.cli.oracle_operator_runtime_commands import register_oracle_operator_runtime_commands
from strategy_validator.cli.oracle_temporal_commands import register_oracle_temporal_commands
from strategy_validator.cli.oracle_event_projection_runners import (
    cmd_oracle_derived_view,
    cmd_oracle_event_checkpoint,
    cmd_oracle_event_log_append,
    cmd_oracle_horizon_checkpoint,
    cmd_oracle_horizon_view,
    cmd_oracle_rolling_review,
    cmd_oracle_rolling_review_checkpoint,
    cmd_verify_oracle_event_checkpoint,
)
from strategy_validator.cli.oracle_event_constitutional_runners import (
    cmd_oracle_annual_lane_append,
    cmd_oracle_annual_review,
    cmd_oracle_annual_review_evidence,
    cmd_oracle_briefing_pack,
    cmd_oracle_constitutional_digest,
    cmd_oracle_constitutional_digest_evidence,
    cmd_oracle_constitutional_gate,
    cmd_oracle_constitutional_lane_append,
    cmd_oracle_diagnose,
    cmd_oracle_doctrine_drift,
    cmd_oracle_doctrine_drift_evidence,
    cmd_oracle_doctrine_lane_append,
    cmd_oracle_doctrine_lineage_index,
    cmd_oracle_doctrine_lineage_verify,
    cmd_oracle_explain,
    cmd_oracle_incident_pack,
    cmd_oracle_memory_append,
    cmd_oracle_memory_review,
    cmd_oracle_memory_review_evidence,
    cmd_oracle_memory_summary,
    cmd_oracle_monthly_digest,
    cmd_oracle_monthly_digest_evidence,
    cmd_oracle_monthly_lane_append,
    cmd_oracle_quarterly_lane_append,
    cmd_oracle_quarterly_review,
    cmd_oracle_quarterly_review_evidence,
    cmd_oracle_replay_audit,
    cmd_oracle_review_lane_append,
    cmd_oracle_semiannual_audit,
    cmd_oracle_semiannual_audit_evidence,
    cmd_oracle_semiannual_lane_append,
    cmd_oracle_status_pack,
    cmd_oracle_transition,
    cmd_oracle_transition_evidence,
    cmd_oracle_weekly_digest,
    cmd_oracle_weekly_digest_evidence,
    cmd_verify_oracle_annual_review_evidence,
    cmd_verify_oracle_constitutional_digest_evidence,
    cmd_verify_oracle_doctrine_drift_evidence,
    cmd_verify_oracle_memory_review_evidence,
    cmd_verify_oracle_monthly_digest_evidence,
    cmd_verify_oracle_quarterly_review_evidence,
    cmd_verify_oracle_semiannual_audit_evidence,
    cmd_verify_oracle_transition_evidence,
    cmd_verify_oracle_weekly_digest_evidence,
    cmd_oracle_compacted_state_inspect,
    cmd_oracle_compacted_state_rebuild,
)
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


from strategy_validator.cli.oracle_temporal_runners import (
    cmd_append_temporal_canonicalization_event_log,
    cmd_canonicalize_temporal_semantic_batch,
    cmd_canonicalize_temporal_semantic_batch_openbb,
    cmd_extract_temporal_semantic_batch,
    cmd_fetch_openbb_temporal_sensor_inputs,
    cmd_verify_temporal_semantic_batch,
    cmd_summarize_temporal_lane,
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
    "cmd_oracle_strategic_memory_horizon": cmd_oracle_strategic_memory_horizon,
    "cmd_oracle_contradiction_resolution": cmd_oracle_contradiction_resolution,
    "cmd_oracle_strategic_intervention": cmd_oracle_strategic_intervention,
    "cmd_oracle_strategic_campaign": cmd_oracle_strategic_campaign,
    "cmd_oracle_strategic_campaign_execution": cmd_oracle_strategic_campaign_execution,
    "cmd_oracle_evidence": cmd_oracle_evidence,
    "cmd_verify_oracle_evidence": cmd_verify_oracle_evidence,
    "cmd_oracle_scenario_lab": cmd_oracle_scenario_lab,
    "cmd_oracle_strategy_cohort": cmd_oracle_strategy_cohort,
    "cmd_oracle_doctrine_adaptation": cmd_oracle_doctrine_adaptation,
    "cmd_oracle_research_execution_memory": cmd_oracle_research_execution_memory,
    "cmd_oracle_strategic_narrative": cmd_oracle_strategic_narrative,
    "cmd_oracle_research_planner": cmd_oracle_research_planner,
    "cmd_oracle_thesis_graph": cmd_oracle_thesis_graph,
    "cmd_oracle_strategic_tension": cmd_oracle_strategic_tension,
}

EVENT_RUNNERS = {
    "oracle-event-log-append": cmd_oracle_event_log_append,
    "oracle-derived-view": cmd_oracle_derived_view,
    "oracle-horizon-view": cmd_oracle_horizon_view,
    "oracle-rolling-review": cmd_oracle_rolling_review,
    "oracle-rolling-review-checkpoint": cmd_oracle_rolling_review_checkpoint,
    "oracle-event-checkpoint": cmd_oracle_event_checkpoint,
    "oracle-horizon-checkpoint": cmd_oracle_horizon_checkpoint,
    "verify-oracle-event-checkpoint": cmd_verify_oracle_event_checkpoint,
    "oracle-transition-evidence": cmd_oracle_transition_evidence,
    "verify-oracle-transition-evidence": cmd_verify_oracle_transition_evidence,
    "oracle-memory-append": cmd_oracle_memory_append,
    "oracle-memory-summary": cmd_oracle_memory_summary,
    "oracle-memory-review": cmd_oracle_memory_review,
    "oracle-memory-review-evidence": cmd_oracle_memory_review_evidence,
    "verify-oracle-memory-review-evidence": cmd_verify_oracle_memory_review_evidence,
    "oracle-review-lane-append": cmd_oracle_review_lane_append,
    "oracle-weekly-digest": cmd_oracle_weekly_digest,
    "oracle-weekly-digest-evidence": cmd_oracle_weekly_digest_evidence,
    "verify-oracle-weekly-digest-evidence": cmd_verify_oracle_weekly_digest_evidence,
    "oracle-doctrine-drift": cmd_oracle_doctrine_drift,
    "oracle-doctrine-drift-evidence": cmd_oracle_doctrine_drift_evidence,
    "verify-oracle-doctrine-drift-evidence": cmd_verify_oracle_doctrine_drift_evidence,
    "oracle-doctrine-lane-append": cmd_oracle_doctrine_lane_append,
    "oracle-monthly-digest": cmd_oracle_monthly_digest,
    "oracle-monthly-digest-evidence": cmd_oracle_monthly_digest_evidence,
    "verify-oracle-monthly-digest-evidence": cmd_verify_oracle_monthly_digest_evidence,
    "oracle-monthly-lane-append": cmd_oracle_monthly_lane_append,
    "oracle-quarterly-review": cmd_oracle_quarterly_review,
    "oracle-quarterly-review-evidence": cmd_oracle_quarterly_review_evidence,
    "verify-oracle-quarterly-review-evidence": cmd_verify_oracle_quarterly_review_evidence,
    "oracle-quarterly-lane-append": cmd_oracle_quarterly_lane_append,
    "oracle-semiannual-audit": cmd_oracle_semiannual_audit,
    "oracle-semiannual-audit-evidence": cmd_oracle_semiannual_audit_evidence,
    "verify-oracle-semiannual-audit-evidence": cmd_verify_oracle_semiannual_audit_evidence,
    "oracle-semiannual-lane-append": cmd_oracle_semiannual_lane_append,
    "oracle-annual-review": cmd_oracle_annual_review,
    "oracle-annual-review-evidence": cmd_oracle_annual_review_evidence,
    "verify-oracle-annual-review-evidence": cmd_verify_oracle_annual_review_evidence,
    "oracle-annual-lane-append": cmd_oracle_annual_lane_append,
    "oracle-constitutional-digest": cmd_oracle_constitutional_digest,
    "oracle-constitutional-digest-evidence": cmd_oracle_constitutional_digest_evidence,
    "verify-oracle-constitutional-digest-evidence": cmd_verify_oracle_constitutional_digest_evidence,
    "oracle-constitutional-lane-append": cmd_oracle_constitutional_lane_append,
    "oracle-doctrine-lineage-index": cmd_oracle_doctrine_lineage_index,
    "oracle-doctrine-lineage-verify": cmd_oracle_doctrine_lineage_verify,
    "oracle-constitutional-gate": cmd_oracle_constitutional_gate,
    "oracle-explain": cmd_oracle_explain,
    "oracle-diagnose": cmd_oracle_diagnose,
    "oracle-status-pack": cmd_oracle_status_pack,
    "oracle-incident-pack": cmd_oracle_incident_pack,
    "oracle-compacted-state-inspect": cmd_oracle_compacted_state_inspect,
    "oracle-compacted-state-rebuild": cmd_oracle_compacted_state_rebuild,
    "oracle-briefing-pack": cmd_oracle_briefing_pack,
    "oracle-replay-audit": cmd_oracle_replay_audit,
    "oracle-transition": cmd_oracle_transition,
}

TEMPORAL_RUNNERS = {
    "append-temporal-canonicalization-event-log": cmd_append_temporal_canonicalization_event_log,
    "extract-temporal-semantic-batch": cmd_extract_temporal_semantic_batch,
    "verify-temporal-semantic-batch": cmd_verify_temporal_semantic_batch,
    "canonicalize-temporal-semantic-batch": cmd_canonicalize_temporal_semantic_batch,
    "summarize-temporal-lane": cmd_summarize_temporal_lane,
    "fetch-openbb-temporal-sensor-inputs": cmd_fetch_openbb_temporal_sensor_inputs,
    "canonicalize-temporal-semantic-batch-openbb": cmd_canonicalize_temporal_semantic_batch_openbb,
}

BRIEFING_REPLAY_RUNNERS = {
    "oracle-compacted-state-inspect": cmd_oracle_compacted_state_inspect,
    "oracle-compacted-state-rebuild": cmd_oracle_compacted_state_rebuild,
    "oracle-briefing-pack": cmd_oracle_briefing_pack,
    "oracle-replay-audit": cmd_oracle_replay_audit,
    "oracle-transition": cmd_oracle_transition,
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Controlled rollout operations tooling")
    sub = parser.add_subparsers(dest="cmd", required=True)

    register_rollout_closure_commands(sub)
    register_oracle_strategy_reporting_commands(sub, runners=STRATEGY_RUNNERS)
    register_oracle_event_constitutional_commands(sub, runners=EVENT_RUNNERS)
    register_oracle_projection_commands(sub, runners={"oracle-projection-artifact-query": cmd_oracle_projection_artifact_query})
    register_oracle_operator_runtime_commands(sub)
    register_oracle_temporal_commands(sub, runners=TEMPORAL_RUNNERS)
    register_oracle_briefing_replay_commands(sub, runners=BRIEFING_REPLAY_RUNNERS)

    ns = parser.parse_args(argv)
    return int(ns._run(ns))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
