from __future__ import annotations

from tests.constitutional.test_boundaries import PKG_ROOT


def test_rollout_ops_prefers_application_reporting_surfaces() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')

    assert 'from strategy_validator.application import (' not in rollout_ops
    assert 'from strategy_validator.cli.oracle_strategy_reporting_runners import (' in rollout_ops
    assert 'from strategy_validator.cli.oracle_event_constitutional_runners import (' in rollout_ops
    assert 'from strategy_validator.cli.oracle_event_projection_runners import (' in rollout_ops
    assert 'from strategy_validator.cli.oracle_rollout_legacy_helpers import (' not in rollout_ops

    assert 'cmd_oracle_strategic_briefing' in rollout_ops
    assert 'cmd_oracle_opportunity_queue' in rollout_ops
    assert 'cmd_oracle_strategy_health_posterior' in rollout_ops
    assert 'cmd_oracle_replay_audit' in rollout_ops
    assert 'cmd_oracle_constitutional_gate' in rollout_ops
    assert 'cmd_oracle_event_checkpoint' in rollout_ops

    assert 'from strategy_validator.validator.oracle_briefing import (' not in rollout_ops
    assert 'from strategy_validator.validator.oracle_advisory import (' not in rollout_ops
    assert 'from strategy_validator.validator.oracle_sensors import load_sensor_ingestion_input' not in rollout_ops
    assert 'from strategy_validator.validator.oracle_trust import (' not in rollout_ops
    assert 'from strategy_validator.validator.oracle_explain import (' not in rollout_ops
    assert 'from strategy_validator.validator.oracle_replay import (' not in rollout_ops
    assert 'from strategy_validator.projections.oracle_event_views import (' not in rollout_ops
