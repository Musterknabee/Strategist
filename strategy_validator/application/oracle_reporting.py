from __future__ import annotations

"""Compatibility reporting shim.

This module preserves the historic ``oracle_reporting`` surface for callers and
monkeypatch-heavy tests, but the bounded application surface now lives in the
split modules:

- ``oracle_operational_surfaces``
- ``oracle_strategy_surfaces``
- ``oracle_advisory_surfaces``
- ``oracle_event_surfaces``

New work should land in those bounded modules instead of expanding this file.
"""

# NOTE: these direct imports intentionally remain local compatibility seams for
# tests that monkeypatch validator helper names on this module.
from strategy_validator.validator.oracle_opportunity_queue import (
    build_oracle_opportunity_queue_report,
    render_oracle_opportunity_queue_markdown,
)
from strategy_validator.validator.oracle_strategic_narrative import (
    build_oracle_strategic_narrative_report,
    render_oracle_strategic_narrative_markdown,
)
from strategy_validator.validator.oracle_strategic_memory_horizon import (
    build_oracle_strategic_memory_horizon_report,
    render_oracle_strategic_memory_horizon_markdown,
)
from strategy_validator.validator.oracle_campaign_planner import (
    build_oracle_strategic_campaign_report,
    render_oracle_strategic_campaign_markdown,
)
from strategy_validator.validator.oracle_campaign_execution import (
    build_oracle_strategic_campaign_execution_report,
    render_oracle_strategic_campaign_execution_markdown,
)
from strategy_validator.validator.oracle_thesis_memory import (
    build_oracle_thesis_memory_report,
    render_oracle_thesis_memory_markdown,
)
from strategy_validator.validator.oracle_scenario_lab import (
    build_oracle_scenario_lab_report,
    render_oracle_scenario_lab_markdown,
)
from strategy_validator.validator.oracle_doctrine_adaptation import (
    build_oracle_doctrine_adaptation_report,
    render_oracle_doctrine_adaptation_markdown,
)
from strategy_validator.validator.oracle_research_execution_memory import (
    build_oracle_research_execution_memory_report,
    render_oracle_research_execution_memory_markdown,
)
from strategy_validator.validator.oracle_strategy_cohort import (
    build_oracle_strategy_cohort_report,
    render_oracle_strategy_cohort_markdown,
)
from strategy_validator.validator.strategy_health_posterior import (
    build_strategy_health_posterior_report,
    render_strategy_health_posterior_markdown,
)
from strategy_validator.validator.oracle_regime_transition import (
    compare_strategic_fusion_reports,
    render_oracle_regime_transition_markdown,
)
from strategy_validator.validator.oracle_contradiction_resolution import (
    build_oracle_contradiction_resolution_report,
    render_oracle_contradiction_resolution_markdown,
)
from strategy_validator.validator.oracle_intervention_simulator import (
    build_oracle_strategic_intervention_report,
    render_oracle_strategic_intervention_markdown,
)
from strategy_validator.validator.oracle_research_planner import (
    build_oracle_research_priority_report,
    render_oracle_research_priority_markdown,
)
from strategy_validator.validator.oracle_thesis_graph import (
    build_oracle_thesis_graph_report,
    render_oracle_thesis_graph_markdown,
)
from strategy_validator.validator.oracle_strategic_tension import (
    build_oracle_strategic_tension_report,
    render_oracle_strategic_tension_markdown,
)
from strategy_validator.validator.oracle_event_log import (
    build_oracle_event_checkpoint_bundle,
    generate_oracle_derived_view,
    generate_oracle_rolling_review,
    render_oracle_derived_view_markdown,
    render_oracle_event_checkpoint_markdown,
    render_oracle_rolling_review_markdown,
    verify_oracle_event_checkpoint_bundle,
)
from strategy_validator.validator.oracle_transition import (
    compare_oracle_evidence,
    generate_oracle_weekly_digest,
    render_oracle_memory_review_markdown,
    render_oracle_state_transition_markdown,
    render_oracle_weekly_digest_markdown,
    review_oracle_memory_lane,
)
from strategy_validator.validator.oracle_constitutional import (
    generate_oracle_constitutional_gate,
    generate_oracle_doctrine_lineage_index,
    render_oracle_constitutional_gate_markdown,
    render_oracle_doctrine_lineage_index_markdown,
)
from strategy_validator.validator.oracle_advisory import (
    build_oracle_evidence_bundle,
    load_oracle_input,
    verify_oracle_evidence_bundle,
)
from strategy_validator.validator.oracle_sensors import load_sensor_ingestion_input
from strategy_validator.validator.oracle_strategic_briefing import load_fusion_report
from strategy_validator.validator.oracle_explain import (
    explain_checkpoint_from_paths,
    render_oracle_explanation_markdown,
)
from strategy_validator.validator.oracle_replay import (
    inspect_oracle_compacted_state,
    render_oracle_compacted_state_inspection_markdown,
)
from strategy_validator.validator.oracle_trust import render_oracle_trust_banner
from strategy_validator.projections.oracle_event_views import emit_oracle_event_view_projection_registry

from strategy_validator.application.oracle_operational_surfaces import *  # noqa: F401,F403
from strategy_validator.application.oracle_strategy_surfaces import *  # noqa: F401,F403
from strategy_validator.application.oracle_advisory_surfaces import *  # noqa: F401,F403
from strategy_validator.application.oracle_event_surfaces import *  # noqa: F401,F403

_COMPAT_TARGETS = {
    'build_opportunity_queue_payload': 'build_oracle_opportunity_queue_report',
    'render_opportunity_queue_markdown_payload': 'render_oracle_opportunity_queue_markdown',
    'build_strategy_cohort_payload': 'build_oracle_strategy_cohort_report',
    'render_strategy_cohort_markdown_payload': 'render_oracle_strategy_cohort_markdown',
    'build_strategic_narrative_payload': 'build_oracle_strategic_narrative_report',
    'render_strategic_narrative_markdown_payload': 'render_oracle_strategic_narrative_markdown',
    'build_strategic_memory_horizon_payload': 'build_oracle_strategic_memory_horizon_report',
    'render_strategic_memory_horizon_markdown_payload': 'render_oracle_strategic_memory_horizon_markdown',
    'build_strategic_campaign_payload': 'build_oracle_strategic_campaign_report',
    'render_strategic_campaign_markdown_payload': 'render_oracle_strategic_campaign_markdown',
    'build_strategic_campaign_execution_payload': 'build_oracle_strategic_campaign_execution_report',
    'render_strategic_campaign_execution_markdown_payload': 'render_oracle_strategic_campaign_execution_markdown',
    'build_thesis_memory_payload': 'build_oracle_thesis_memory_report',
    'render_thesis_memory_markdown_payload': 'render_oracle_thesis_memory_markdown',
    'build_scenario_lab_payload': 'build_oracle_scenario_lab_report',
    'render_scenario_lab_markdown_payload': 'render_oracle_scenario_lab_markdown',
    'build_doctrine_adaptation_payload': 'build_oracle_doctrine_adaptation_report',
    'render_doctrine_adaptation_markdown_payload': 'render_oracle_doctrine_adaptation_markdown',
    'build_research_execution_memory_payload': 'build_oracle_research_execution_memory_report',
    'render_research_execution_memory_markdown_payload': 'render_oracle_research_execution_memory_markdown',
    'build_strategy_health_posterior_payload': 'build_strategy_health_posterior_report',
    'render_strategy_health_posterior_markdown_payload': 'render_strategy_health_posterior_markdown',
    'build_regime_transition_payload': 'compare_strategic_fusion_reports',
    'render_regime_transition_markdown_payload': 'render_oracle_regime_transition_markdown',
    'build_contradiction_resolution_payload': 'build_oracle_contradiction_resolution_report',
    'render_contradiction_resolution_markdown_payload': 'render_oracle_contradiction_resolution_markdown',
    'build_strategic_intervention_payload': 'build_oracle_strategic_intervention_report',
    'render_strategic_intervention_markdown_payload': 'render_oracle_strategic_intervention_markdown',
    'build_research_priority_payload': 'build_oracle_research_priority_report',
    'render_research_priority_markdown_payload': 'render_oracle_research_priority_markdown',
    'build_thesis_graph_payload': 'build_oracle_thesis_graph_report',
    'render_thesis_graph_markdown_payload': 'render_oracle_thesis_graph_markdown',
    'build_strategic_tension_payload': 'build_oracle_strategic_tension_report',
    'render_strategic_tension_markdown_payload': 'render_oracle_strategic_tension_markdown',
    'build_event_checkpoint_payload': 'build_oracle_event_checkpoint_bundle',
    'render_event_checkpoint_markdown_payload': 'render_oracle_event_checkpoint_markdown',
    'verify_event_checkpoint_payload': 'verify_oracle_event_checkpoint_bundle',
    'build_derived_view_payload': 'generate_oracle_derived_view',
    'render_derived_view_markdown_payload': 'render_oracle_derived_view_markdown',
    'build_rolling_review_payload': 'generate_oracle_rolling_review',
    'render_rolling_review_markdown_payload': 'render_oracle_rolling_review_markdown',
    'build_state_transition_payload': 'compare_oracle_evidence',
    'render_state_transition_markdown_payload': 'render_oracle_state_transition_markdown',
    'build_memory_review_payload': 'review_oracle_memory_lane',
    'render_memory_review_markdown_payload': 'render_oracle_memory_review_markdown',
    'build_weekly_digest_payload': 'generate_oracle_weekly_digest',
    'render_weekly_digest_markdown_payload': 'render_oracle_weekly_digest_markdown',
    'build_constitutional_gate_payload': 'generate_oracle_constitutional_gate',
    'render_constitutional_gate_markdown_payload': 'render_oracle_constitutional_gate_markdown',
    'build_doctrine_lineage_index_payload': 'generate_oracle_doctrine_lineage_index',
    'render_doctrine_lineage_index_markdown_payload': 'render_oracle_doctrine_lineage_index_markdown',
    'load_sensor_ingestion_input_payload': 'load_sensor_ingestion_input',
    'load_fusion_report_payload': 'load_fusion_report',
    'build_oracle_evidence_bundle_payload': 'build_oracle_evidence_bundle',
    'load_oracle_input_payload': 'load_oracle_input',
    'verify_oracle_evidence_bundle_payload': 'verify_oracle_evidence_bundle',
    'render_oracle_trust_banner_payload': 'render_oracle_trust_banner',
    'explain_checkpoint_from_paths_payload': 'explain_checkpoint_from_paths',
    'render_oracle_explanation_markdown_payload': 'render_oracle_explanation_markdown',
    'emit_event_view_projection_registry_payload': 'emit_oracle_event_view_projection_registry',
    'inspect_compacted_state_payload': 'inspect_oracle_compacted_state',
    'render_compacted_state_inspection_markdown_payload': 'render_oracle_compacted_state_inspection_markdown',
}


def _make_payload(target_name: str):
    def _payload(*args, **kwargs):
        return globals()[target_name](*args, **kwargs)

    return _payload


for _payload_name, _target_name in _COMPAT_TARGETS.items():
    globals()[_payload_name] = _make_payload(_target_name)
    globals()[_payload_name].__name__ = _payload_name
    globals()[_payload_name].__qualname__ = _payload_name
    globals()[_payload_name].__doc__ = f"Compatibility payload wrapper for ``{_target_name}``."
