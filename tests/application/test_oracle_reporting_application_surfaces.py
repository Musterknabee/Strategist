from __future__ import annotations

from strategy_validator.application import (
    append_event_log_entry_payload,
    build_briefing_pack_payload,
    build_replay_audit_payload,
    build_strategic_briefing_payload,
    emit_briefing_pack_projection_registry_payload,
    materialize_briefing_pack_payload,
    render_briefing_pack_html_payload,
    render_briefing_pack_markdown_payload,
    render_replay_audit_markdown_payload,
    render_strategic_briefing_markdown_payload,
    build_strategy_health_posterior_payload,
    render_strategy_health_posterior_markdown_payload,
    build_regime_transition_payload,
    render_regime_transition_markdown_payload,
    build_contradiction_resolution_payload,
    render_contradiction_resolution_markdown_payload,
    build_strategic_intervention_payload,
    render_strategic_intervention_markdown_payload,
    build_research_priority_payload,
    render_research_priority_markdown_payload,
    build_thesis_graph_payload,
    render_thesis_graph_markdown_payload,
    build_strategic_tension_payload,
    render_strategic_tension_markdown_payload,
    build_event_checkpoint_payload,
    render_event_checkpoint_markdown_payload,
    verify_event_checkpoint_payload,
    build_derived_view_payload,
    render_derived_view_markdown_payload,
    build_rolling_review_payload,
    render_rolling_review_markdown_payload,
    build_state_transition_payload,
    render_state_transition_markdown_payload,
    build_memory_review_payload,
    render_memory_review_markdown_payload,
    build_weekly_digest_payload,
    render_weekly_digest_markdown_payload,
    build_constitutional_gate_payload,
    render_constitutional_gate_markdown_payload,
    build_doctrine_lineage_index_payload,
    render_doctrine_lineage_index_markdown_payload,
)


def test_oracle_reporting_surfaces_are_importable() -> None:
    assert callable(build_briefing_pack_payload)
    assert callable(materialize_briefing_pack_payload)
    assert callable(emit_briefing_pack_projection_registry_payload)
    assert callable(render_briefing_pack_markdown_payload)
    assert callable(render_briefing_pack_html_payload)
    assert callable(build_strategic_briefing_payload)
    assert callable(render_strategic_briefing_markdown_payload)
    assert callable(build_replay_audit_payload)
    assert callable(render_replay_audit_markdown_payload)
    assert callable(append_event_log_entry_payload)
    assert callable(build_strategy_health_posterior_payload)
    assert callable(render_strategy_health_posterior_markdown_payload)
    assert callable(build_regime_transition_payload)
    assert callable(render_regime_transition_markdown_payload)
    assert callable(build_contradiction_resolution_payload)
    assert callable(render_contradiction_resolution_markdown_payload)
    assert callable(build_strategic_intervention_payload)
    assert callable(render_strategic_intervention_markdown_payload)
    assert callable(build_research_priority_payload)
    assert callable(render_research_priority_markdown_payload)
    assert callable(build_thesis_graph_payload)
    assert callable(render_thesis_graph_markdown_payload)
    assert callable(build_strategic_tension_payload)
    assert callable(render_strategic_tension_markdown_payload)
    assert callable(build_event_checkpoint_payload)
    assert callable(render_event_checkpoint_markdown_payload)
    assert callable(verify_event_checkpoint_payload)
    assert callable(build_derived_view_payload)
    assert callable(render_derived_view_markdown_payload)
    assert callable(build_rolling_review_payload)
    assert callable(render_rolling_review_markdown_payload)
    assert callable(build_state_transition_payload)
    assert callable(render_state_transition_markdown_payload)
    assert callable(build_memory_review_payload)
    assert callable(render_memory_review_markdown_payload)
    assert callable(build_weekly_digest_payload)
    assert callable(render_weekly_digest_markdown_payload)
    assert callable(build_constitutional_gate_payload)
    assert callable(render_constitutional_gate_markdown_payload)
    assert callable(build_doctrine_lineage_index_payload)
    assert callable(render_doctrine_lineage_index_markdown_payload)


def test_extended_reporting_payload_helpers_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_reporting as reporting

    monkeypatch.setattr(reporting, 'build_oracle_opportunity_queue_report', lambda **kwargs: {'kind': 'queue', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_opportunity_queue_markdown', lambda report: f"queue:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategy_cohort_report', lambda **kwargs: {'kind': 'cohort', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategy_cohort_markdown', lambda report: f"cohort:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategic_narrative_report', lambda **kwargs: {'kind': 'narrative', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_narrative_markdown', lambda report: f"narrative:{report['kind']}")

    assert reporting.build_opportunity_queue_payload(alpha=1)['kind'] == 'queue'
    assert reporting.render_opportunity_queue_markdown_payload({'kind': 'queue'}) == 'queue:queue'
    assert reporting.build_strategy_cohort_payload(beta=2)['kind'] == 'cohort'
    assert reporting.render_strategy_cohort_markdown_payload({'kind': 'cohort'}) == 'cohort:cohort'
    assert reporting.build_strategic_narrative_payload(gamma=3)['kind'] == 'narrative'
    assert reporting.render_strategic_narrative_markdown_payload({'kind': 'narrative'}) == 'narrative:narrative'

    monkeypatch.setattr(reporting, 'build_oracle_strategic_memory_horizon_report', lambda **kwargs: {'kind': 'memory_horizon', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_memory_horizon_markdown', lambda report: f"memory_horizon:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategic_campaign_report', lambda **kwargs: {'kind': 'campaign', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_campaign_markdown', lambda report: f"campaign:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategic_campaign_execution_report', lambda **kwargs: {'kind': 'campaign_execution', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_campaign_execution_markdown', lambda report: f"campaign_execution:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_thesis_memory_report', lambda **kwargs: {'kind': 'thesis_memory', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_thesis_memory_markdown', lambda report: f"thesis_memory:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_scenario_lab_report', lambda **kwargs: {'kind': 'scenario_lab', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_scenario_lab_markdown', lambda report: f"scenario_lab:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_doctrine_adaptation_report', lambda **kwargs: {'kind': 'doctrine', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_doctrine_adaptation_markdown', lambda report: f"doctrine:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_research_execution_memory_report', lambda **kwargs: {'kind': 'execution_memory', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_research_execution_memory_markdown', lambda report: f"execution_memory:{report['kind']}")

    assert reporting.build_strategic_memory_horizon_payload(delta=4)['kind'] == 'memory_horizon'
    assert reporting.render_strategic_memory_horizon_markdown_payload({'kind': 'memory_horizon'}) == 'memory_horizon:memory_horizon'
    assert reporting.build_strategic_campaign_payload(epsilon=5)['kind'] == 'campaign'
    assert reporting.render_strategic_campaign_markdown_payload({'kind': 'campaign'}) == 'campaign:campaign'
    assert reporting.build_strategic_campaign_execution_payload(zeta=6)['kind'] == 'campaign_execution'
    assert reporting.render_strategic_campaign_execution_markdown_payload({'kind': 'campaign_execution'}) == 'campaign_execution:campaign_execution'
    assert reporting.build_thesis_memory_payload(eta=7)['kind'] == 'thesis_memory'
    assert reporting.render_thesis_memory_markdown_payload({'kind': 'thesis_memory'}) == 'thesis_memory:thesis_memory'
    assert reporting.build_scenario_lab_payload(theta=8)['kind'] == 'scenario_lab'
    assert reporting.render_scenario_lab_markdown_payload({'kind': 'scenario_lab'}) == 'scenario_lab:scenario_lab'
    assert reporting.build_doctrine_adaptation_payload(iota=9)['kind'] == 'doctrine'
    assert reporting.render_doctrine_adaptation_markdown_payload({'kind': 'doctrine'}) == 'doctrine:doctrine'
    assert reporting.build_research_execution_memory_payload(kappa=10)['kind'] == 'execution_memory'
    assert reporting.render_research_execution_memory_markdown_payload({'kind': 'execution_memory'}) == 'execution_memory:execution_memory'



def test_advanced_reporting_payload_helpers_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_reporting as reporting

    monkeypatch.setattr(reporting, 'build_strategy_health_posterior_report', lambda **kwargs: {'kind': 'posterior', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_strategy_health_posterior_markdown', lambda report: f"posterior:{report['kind']}")
    monkeypatch.setattr(reporting, 'compare_strategic_fusion_reports', lambda **kwargs: {'kind': 'transition', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_regime_transition_markdown', lambda report: f"transition:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_contradiction_resolution_report', lambda **kwargs: {'kind': 'contradiction', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_contradiction_resolution_markdown', lambda report: f"contradiction:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategic_intervention_report', lambda **kwargs: {'kind': 'intervention', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_intervention_markdown', lambda report: f"intervention:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_research_priority_report', lambda **kwargs: {'kind': 'priority', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_research_priority_markdown', lambda report: f"priority:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_thesis_graph_report', lambda **kwargs: {'kind': 'graph', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_thesis_graph_markdown', lambda report: f"graph:{report['kind']}")
    monkeypatch.setattr(reporting, 'build_oracle_strategic_tension_report', lambda **kwargs: {'kind': 'tension', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_strategic_tension_markdown', lambda report: f"tension:{report['kind']}")

    assert reporting.build_strategy_health_posterior_payload(mu=1)['kind'] == 'posterior'
    assert reporting.render_strategy_health_posterior_markdown_payload({'kind': 'posterior'}) == 'posterior:posterior'
    assert reporting.build_regime_transition_payload(nu=2)['kind'] == 'transition'
    assert reporting.render_regime_transition_markdown_payload({'kind': 'transition'}) == 'transition:transition'
    assert reporting.build_contradiction_resolution_payload(xi=3)['kind'] == 'contradiction'
    assert reporting.render_contradiction_resolution_markdown_payload({'kind': 'contradiction'}) == 'contradiction:contradiction'
    assert reporting.build_strategic_intervention_payload(omicron=4)['kind'] == 'intervention'
    assert reporting.render_strategic_intervention_markdown_payload({'kind': 'intervention'}) == 'intervention:intervention'
    assert reporting.build_research_priority_payload(pi=5)['kind'] == 'priority'
    assert reporting.render_research_priority_markdown_payload({'kind': 'priority'}) == 'priority:priority'
    assert reporting.build_thesis_graph_payload(rho=6)['kind'] == 'graph'
    assert reporting.render_thesis_graph_markdown_payload({'kind': 'graph'}) == 'graph:graph'
    assert reporting.build_strategic_tension_payload(sigma=7)['kind'] == 'tension'
    assert reporting.render_strategic_tension_markdown_payload({'kind': 'tension'}) == 'tension:tension'


def test_event_transition_and_constitutional_payload_helpers_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_reporting as reporting

    monkeypatch.setattr(reporting, 'build_oracle_event_checkpoint_bundle', lambda **kwargs: {'kind': 'checkpoint', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_event_checkpoint_markdown', lambda report: f"checkpoint:{report['kind']}")
    monkeypatch.setattr(reporting, 'verify_oracle_event_checkpoint_bundle', lambda **kwargs: {'kind': 'verify_checkpoint', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'generate_oracle_derived_view', lambda **kwargs: {'kind': 'derived', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_derived_view_markdown', lambda report: f"derived:{report['kind']}")
    monkeypatch.setattr(reporting, 'generate_oracle_rolling_review', lambda **kwargs: {'kind': 'rolling', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_rolling_review_markdown', lambda report: f"rolling:{report['kind']}")
    monkeypatch.setattr(reporting, 'compare_oracle_evidence', lambda **kwargs: {'kind': 'transition', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_state_transition_markdown', lambda report: f"transition:{report['kind']}")
    monkeypatch.setattr(reporting, 'review_oracle_memory_lane', lambda **kwargs: {'kind': 'memory_review', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_memory_review_markdown', lambda report: f"memory_review:{report['kind']}")
    monkeypatch.setattr(reporting, 'generate_oracle_weekly_digest', lambda **kwargs: {'kind': 'weekly', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_weekly_digest_markdown', lambda report: f"weekly:{report['kind']}")
    monkeypatch.setattr(reporting, 'generate_oracle_constitutional_gate', lambda **kwargs: {'kind': 'gate', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_constitutional_gate_markdown', lambda report: f"gate:{report['kind']}")
    monkeypatch.setattr(reporting, 'generate_oracle_doctrine_lineage_index', lambda **kwargs: {'kind': 'lineage', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_doctrine_lineage_index_markdown', lambda report: f"lineage:{report['kind']}")

    assert reporting.build_event_checkpoint_payload(a=1)['kind'] == 'checkpoint'
    assert reporting.render_event_checkpoint_markdown_payload({'kind': 'checkpoint'}) == 'checkpoint:checkpoint'
    assert reporting.verify_event_checkpoint_payload(b=2)['kind'] == 'verify_checkpoint'
    assert reporting.build_derived_view_payload(c=3)['kind'] == 'derived'
    assert reporting.render_derived_view_markdown_payload({'kind': 'derived'}) == 'derived:derived'
    assert reporting.build_rolling_review_payload(d=4)['kind'] == 'rolling'
    assert reporting.render_rolling_review_markdown_payload({'kind': 'rolling'}) == 'rolling:rolling'
    assert reporting.build_state_transition_payload(e=5)['kind'] == 'transition'
    assert reporting.render_state_transition_markdown_payload({'kind': 'transition'}) == 'transition:transition'
    assert reporting.build_memory_review_payload(f=6)['kind'] == 'memory_review'
    assert reporting.render_memory_review_markdown_payload({'kind': 'memory_review'}) == 'memory_review:memory_review'
    assert reporting.build_weekly_digest_payload(g=7)['kind'] == 'weekly'
    assert reporting.render_weekly_digest_markdown_payload({'kind': 'weekly'}) == 'weekly:weekly'
    assert reporting.build_constitutional_gate_payload(h=8)['kind'] == 'gate'
    assert reporting.render_constitutional_gate_markdown_payload({'kind': 'gate'}) == 'gate:gate'
    assert reporting.build_doctrine_lineage_index_payload(i=9)['kind'] == 'lineage'
    assert reporting.render_doctrine_lineage_index_markdown_payload({'kind': 'lineage'}) == 'lineage:lineage'


def test_loader_trust_and_replay_payload_helpers_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_reporting as reporting

    monkeypatch.setattr(reporting, 'load_sensor_ingestion_input', lambda *args, **kwargs: {'kind': 'sensor_load', 'args': args, 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'load_fusion_report', lambda *args, **kwargs: {'kind': 'fusion_load', 'args': args, 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'build_oracle_evidence_bundle', lambda **kwargs: {'kind': 'bundle', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'verify_oracle_evidence_bundle', lambda **kwargs: {'kind': 'verify_bundle', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'render_oracle_trust_banner', lambda *args, **kwargs: 'trust-banner')
    monkeypatch.setattr(reporting, 'explain_checkpoint_from_paths', lambda *args, **kwargs: {'kind': 'explain_checkpoint'})
    monkeypatch.setattr(reporting, 'render_oracle_explanation_markdown', lambda payload: f"explain:{payload['kind']}")
    monkeypatch.setattr(reporting, 'emit_oracle_event_view_projection_registry', lambda **kwargs: {'kind': 'emit_view', 'kwargs': kwargs})
    monkeypatch.setattr(reporting, 'inspect_oracle_compacted_state', lambda *args, **kwargs: {'kind': 'inspect_compacted'})
    monkeypatch.setattr(reporting, 'render_oracle_compacted_state_inspection_markdown', lambda payload: f"inspect:{payload['kind']}")

    assert reporting.load_sensor_ingestion_input_payload('a')['kind'] == 'sensor_load'
    assert reporting.load_fusion_report_payload('b')['kind'] == 'fusion_load'
    assert reporting.build_oracle_evidence_bundle_payload(alpha=1)['kind'] == 'bundle'
    assert reporting.verify_oracle_evidence_bundle_payload(beta=2)['kind'] == 'verify_bundle'
    assert reporting.render_oracle_trust_banner_payload('x') == 'trust-banner'
    assert reporting.explain_checkpoint_from_paths_payload('c')['kind'] == 'explain_checkpoint'
    assert reporting.render_oracle_explanation_markdown_payload({'kind': 'demo'}) == 'explain:demo'
    assert reporting.emit_event_view_projection_registry_payload(delta=4)['kind'] == 'emit_view'
    assert reporting.inspect_compacted_state_payload('z')['kind'] == 'inspect_compacted'
    assert reporting.render_compacted_state_inspection_markdown_payload({'kind': 'inspect_compacted'}) == 'inspect:inspect_compacted'
