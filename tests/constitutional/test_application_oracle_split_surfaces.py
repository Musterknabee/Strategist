from __future__ import annotations

from strategy_validator import application


def test_application_root_routes_operational_surfaces_to_dedicated_module() -> None:
    assert application.build_briefing_pack_payload.__module__ == 'strategy_validator.application.oracle_operational_surfaces'
    assert application.render_briefing_pack_markdown_payload.__module__ == 'strategy_validator.application.oracle_operational_surfaces'
    assert application.load_fusion_report_payload.__module__ == 'strategy_validator.application.oracle_operational_surfaces'


def test_application_root_routes_strategy_surfaces_to_dedicated_module() -> None:
    assert application.build_opportunity_queue_payload.__module__ == 'strategy_validator.application.oracle_strategy_surfaces'
    assert application.render_opportunity_queue_markdown_payload.__module__ == 'strategy_validator.application.oracle_strategy_surfaces'
    assert application.build_strategy_health_posterior_payload.__module__ == 'strategy_validator.application.oracle_strategy_surfaces'
    assert application.load_strategic_campaign_report_payload.__module__ == 'strategy_validator.application.oracle_strategy_surfaces'
