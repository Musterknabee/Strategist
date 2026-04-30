from __future__ import annotations

from strategy_validator.validator.oracle_opportunity_queue import (
    build_oracle_opportunity_queue_report,
    render_oracle_opportunity_queue_markdown,
)
from strategy_validator.validator.oracle_strategic_narrative import (
    build_oracle_strategic_narrative_report,
    load_strategic_narrative_report,
    render_oracle_strategic_narrative_markdown,
)
from strategy_validator.validator.oracle_strategic_memory_horizon import (
    build_oracle_strategic_memory_horizon_report,
    load_strategic_memory_horizon_report,
    render_oracle_strategic_memory_horizon_markdown,
)
from strategy_validator.validator.oracle_campaign_planner import (
    build_oracle_strategic_campaign_report,
    load_strategic_campaign_report,
    render_oracle_strategic_campaign_markdown,
)
from strategy_validator.validator.oracle_campaign_execution import (
    build_oracle_strategic_campaign_execution_report,
    load_strategic_campaign_execution_input,
    load_strategic_campaign_execution_report,
    render_oracle_strategic_campaign_execution_markdown,
)
from strategy_validator.validator.oracle_thesis_memory import (
    build_oracle_thesis_memory_report,
    load_thesis_memory_report,
    render_oracle_thesis_memory_markdown,
)
from strategy_validator.validator.oracle_scenario_lab import (
    build_oracle_scenario_lab_report,
    load_scenario_plan_input,
    render_oracle_scenario_lab_markdown,
)
from strategy_validator.validator.oracle_doctrine_adaptation import (
    build_oracle_doctrine_adaptation_report,
    load_doctrine_adaptation_report,
    render_oracle_doctrine_adaptation_markdown,
)
from strategy_validator.validator.oracle_research_execution_memory import (
    build_oracle_research_execution_memory_report,
    load_investigation_outcome_input,
    load_research_execution_memory_report,
    render_oracle_research_execution_memory_markdown,
)
from strategy_validator.validator.oracle_strategy_cohort import (
    build_oracle_strategy_cohort_report,
    load_strategy_cohort_report,
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
    load_contradiction_resolution_report,
    render_oracle_contradiction_resolution_markdown,
)
from strategy_validator.validator.oracle_intervention_simulator import (
    build_oracle_strategic_intervention_report,
    load_strategic_intervention_report,
    render_oracle_strategic_intervention_markdown,
)
from strategy_validator.validator.oracle_research_planner import (
    build_oracle_research_priority_report,
    load_research_priority_report,
    render_oracle_research_priority_markdown,
)
from strategy_validator.validator.oracle_thesis_graph import (
    build_oracle_thesis_graph_report,
    load_thesis_graph_report,
    render_oracle_thesis_graph_markdown,
)
from strategy_validator.validator.oracle_strategic_tension import (
    build_oracle_strategic_tension_report,
    load_strategic_tension_report,
    render_oracle_strategic_tension_markdown,
)


def build_opportunity_queue_payload(**kwargs):
    return build_oracle_opportunity_queue_report(**kwargs)


def render_opportunity_queue_markdown_payload(report) -> str:
    return render_oracle_opportunity_queue_markdown(report)


def build_strategy_cohort_payload(**kwargs):
    return build_oracle_strategy_cohort_report(**kwargs)


def render_strategy_cohort_markdown_payload(report) -> str:
    return render_oracle_strategy_cohort_markdown(report)


def load_strategy_cohort_report_payload(*args, **kwargs):
    return load_strategy_cohort_report(*args, **kwargs)


def build_strategic_narrative_payload(**kwargs):
    return build_oracle_strategic_narrative_report(**kwargs)


def render_strategic_narrative_markdown_payload(report) -> str:
    return render_oracle_strategic_narrative_markdown(report)


def load_strategic_narrative_report_payload(*args, **kwargs):
    return load_strategic_narrative_report(*args, **kwargs)


def build_strategic_memory_horizon_payload(**kwargs):
    return build_oracle_strategic_memory_horizon_report(**kwargs)


def render_strategic_memory_horizon_markdown_payload(report) -> str:
    return render_oracle_strategic_memory_horizon_markdown(report)


def load_strategic_memory_horizon_report_payload(*args, **kwargs):
    return load_strategic_memory_horizon_report(*args, **kwargs)


def build_strategic_campaign_payload(**kwargs):
    return build_oracle_strategic_campaign_report(**kwargs)


def render_strategic_campaign_markdown_payload(report) -> str:
    return render_oracle_strategic_campaign_markdown(report)


def load_strategic_campaign_report_payload(*args, **kwargs):
    return load_strategic_campaign_report(*args, **kwargs)


def build_strategic_campaign_execution_payload(**kwargs):
    return build_oracle_strategic_campaign_execution_report(**kwargs)


def render_strategic_campaign_execution_markdown_payload(report) -> str:
    return render_oracle_strategic_campaign_execution_markdown(report)


def load_strategic_campaign_execution_input_payload(*args, **kwargs):
    return load_strategic_campaign_execution_input(*args, **kwargs)


def load_strategic_campaign_execution_report_payload(*args, **kwargs):
    return load_strategic_campaign_execution_report(*args, **kwargs)


def build_thesis_memory_payload(**kwargs):
    return build_oracle_thesis_memory_report(**kwargs)


def render_thesis_memory_markdown_payload(report) -> str:
    return render_oracle_thesis_memory_markdown(report)


def load_thesis_memory_report_payload(*args, **kwargs):
    return load_thesis_memory_report(*args, **kwargs)


def build_scenario_lab_payload(**kwargs):
    return build_oracle_scenario_lab_report(**kwargs)


def render_scenario_lab_markdown_payload(report) -> str:
    return render_oracle_scenario_lab_markdown(report)


def load_scenario_plan_input_payload(*args, **kwargs):
    return load_scenario_plan_input(*args, **kwargs)


def build_doctrine_adaptation_payload(**kwargs):
    return build_oracle_doctrine_adaptation_report(**kwargs)


def render_doctrine_adaptation_markdown_payload(report) -> str:
    return render_oracle_doctrine_adaptation_markdown(report)


def load_doctrine_adaptation_report_payload(*args, **kwargs):
    return load_doctrine_adaptation_report(*args, **kwargs)


def build_research_execution_memory_payload(**kwargs):
    return build_oracle_research_execution_memory_report(**kwargs)


def render_research_execution_memory_markdown_payload(report) -> str:
    return render_oracle_research_execution_memory_markdown(report)


def load_investigation_outcome_input_payload(*args, **kwargs):
    return load_investigation_outcome_input(*args, **kwargs)


def load_research_execution_memory_report_payload(*args, **kwargs):
    return load_research_execution_memory_report(*args, **kwargs)


def build_strategy_health_posterior_payload(**kwargs):
    return build_strategy_health_posterior_report(**kwargs)


def render_strategy_health_posterior_markdown_payload(report) -> str:
    return render_strategy_health_posterior_markdown(report)


def build_regime_transition_payload(**kwargs):
    return compare_strategic_fusion_reports(**kwargs)


def render_regime_transition_markdown_payload(report) -> str:
    return render_oracle_regime_transition_markdown(report)


def build_contradiction_resolution_payload(**kwargs):
    return build_oracle_contradiction_resolution_report(**kwargs)


def render_contradiction_resolution_markdown_payload(report) -> str:
    return render_oracle_contradiction_resolution_markdown(report)


def load_contradiction_resolution_report_payload(*args, **kwargs):
    return load_contradiction_resolution_report(*args, **kwargs)


def build_strategic_intervention_payload(**kwargs):
    return build_oracle_strategic_intervention_report(**kwargs)


def render_strategic_intervention_markdown_payload(report) -> str:
    return render_oracle_strategic_intervention_markdown(report)


def load_strategic_intervention_report_payload(*args, **kwargs):
    return load_strategic_intervention_report(*args, **kwargs)


def build_research_priority_payload(**kwargs):
    return build_oracle_research_priority_report(**kwargs)


def render_research_priority_markdown_payload(report) -> str:
    return render_oracle_research_priority_markdown(report)


def load_research_priority_report_payload(*args, **kwargs):
    return load_research_priority_report(*args, **kwargs)


def build_thesis_graph_payload(**kwargs):
    return build_oracle_thesis_graph_report(**kwargs)


def render_thesis_graph_markdown_payload(report) -> str:
    return render_oracle_thesis_graph_markdown(report)


def load_thesis_graph_report_payload(*args, **kwargs):
    return load_thesis_graph_report(*args, **kwargs)


def build_strategic_tension_payload(**kwargs):
    return build_oracle_strategic_tension_report(**kwargs)


def render_strategic_tension_markdown_payload(report) -> str:
    return render_oracle_strategic_tension_markdown(report)


def load_strategic_tension_report_payload(*args, **kwargs):
    return load_strategic_tension_report(*args, **kwargs)
