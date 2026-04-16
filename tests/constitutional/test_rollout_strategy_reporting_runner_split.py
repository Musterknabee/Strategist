from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_strategy_reporting_runners_module_owns_split_runner_cluster() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_strategy_reporting_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_strategy_advisory_runners import (' in helper
    assert 'from strategy_validator.cli.oracle_strategy_domain_runners import (' in helper
    assert 'cmd_oracle_advisory,' in helper
    assert 'cmd_oracle_strategic_briefing,' in helper
    assert 'cmd_oracle_evidence,' in helper
    assert 'def cmd_oracle_advisory(' not in helper
    assert 'def cmd_oracle_strategic_briefing(' not in helper
    assert 'def cmd_oracle_evidence(' not in helper


def test_rollout_ops_imports_strategy_reporting_runners() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_strategy_reporting_runners import (' in rollout_ops
    assert 'cmd_oracle_advisory,' in rollout_ops
    assert 'cmd_oracle_signal_fusion,' in rollout_ops
    assert 'cmd_oracle_strategic_briefing,' in rollout_ops
    assert 'cmd_oracle_evidence,' in rollout_ops
    assert 'def cmd_oracle_advisory(' not in rollout_ops
    assert 'def cmd_oracle_signal_fusion(' not in rollout_ops
    assert 'def cmd_oracle_strategic_briefing(' not in rollout_ops
    assert 'def cmd_oracle_evidence(' not in rollout_ops
