from __future__ import annotations

from strategy_validator.application import (
    build_briefing_pack_payload,
    build_opportunity_queue_payload,
    build_strategy_health_posterior_payload,
    load_fusion_report_payload,
    load_strategic_campaign_report_payload,
    render_briefing_pack_markdown_payload,
    render_opportunity_queue_markdown_payload,
    render_strategy_health_posterior_markdown_payload,
)


def test_oracle_split_surface_exports_are_importable() -> None:
    assert callable(build_briefing_pack_payload)
    assert callable(render_briefing_pack_markdown_payload)
    assert callable(load_fusion_report_payload)
    assert callable(build_opportunity_queue_payload)
    assert callable(render_opportunity_queue_markdown_payload)
    assert callable(load_strategic_campaign_report_payload)
    assert callable(build_strategy_health_posterior_payload)
    assert callable(render_strategy_health_posterior_markdown_payload)


def test_oracle_operational_surface_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_operational_surfaces as ops

    monkeypatch.setattr(ops, 'build_oracle_briefing_pack', lambda **kwargs: {'kind': 'briefing', 'kwargs': kwargs})
    monkeypatch.setattr(ops, 'render_oracle_briefing_pack_markdown', lambda report: f"briefing:{report['kind']}")
    monkeypatch.setattr(ops, 'load_fusion_report', lambda *args, **kwargs: {'kind': 'fusion_load', 'args': args, 'kwargs': kwargs})

    assert ops.build_briefing_pack_payload(alpha=1)['kind'] == 'briefing'
    assert ops.render_briefing_pack_markdown_payload({'kind': 'briefing'}) == 'briefing:briefing'
    assert ops.load_fusion_report_payload('artifact.json')['kind'] == 'fusion_load'


def test_oracle_strategy_surface_round_trip(monkeypatch) -> None:
    import strategy_validator.application.oracle_strategy_surfaces as strategy

    monkeypatch.setattr(strategy, 'build_oracle_opportunity_queue_report', lambda **kwargs: {'kind': 'queue', 'kwargs': kwargs})
    monkeypatch.setattr(strategy, 'render_oracle_opportunity_queue_markdown', lambda report: f"queue:{report['kind']}")
    monkeypatch.setattr(strategy, 'load_strategic_campaign_report', lambda *args, **kwargs: {'kind': 'campaign_load', 'args': args, 'kwargs': kwargs})
    monkeypatch.setattr(strategy, 'build_strategy_health_posterior_report', lambda **kwargs: {'kind': 'posterior', 'kwargs': kwargs})
    monkeypatch.setattr(strategy, 'render_strategy_health_posterior_markdown', lambda report: f"posterior:{report['kind']}")

    assert strategy.build_opportunity_queue_payload(beta=2)['kind'] == 'queue'
    assert strategy.render_opportunity_queue_markdown_payload({'kind': 'queue'}) == 'queue:queue'
    assert strategy.load_strategic_campaign_report_payload('campaign.json')['kind'] == 'campaign_load'
    assert strategy.build_strategy_health_posterior_payload(gamma=3)['kind'] == 'posterior'
    assert strategy.render_strategy_health_posterior_markdown_payload({'kind': 'posterior'}) == 'posterior:posterior'
