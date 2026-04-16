from pathlib import Path


def test_rollout_ops_imports_event_projection_runners_module() -> None:
    content = Path('strategy_validator/cli/rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_projection_runners import (' in content


def test_rollout_ops_no_longer_defines_event_projection_runner_cluster_inline() -> None:
    content = Path('strategy_validator/cli/rollout_ops.py').read_text(encoding='utf-8')
    for symbol in [
        'def cmd_oracle_event_log_append(',
        'def cmd_oracle_rolling_review(',
        'def cmd_oracle_rolling_review_checkpoint(',
        'def cmd_oracle_derived_view(',
        'def cmd_oracle_event_checkpoint(',
        'def cmd_oracle_horizon_view(',
        'def cmd_oracle_horizon_checkpoint(',
        'def cmd_verify_oracle_event_checkpoint(',
    ]:
        assert symbol not in content


def test_event_projection_runner_module_owns_cluster() -> None:
    content = Path('strategy_validator/cli/oracle_event_projection_runners.py').read_text(encoding='utf-8')
    for symbol in [
        'def cmd_oracle_event_log_append(',
        'def cmd_oracle_rolling_review(',
        'def cmd_oracle_rolling_review_checkpoint(',
        'def cmd_oracle_derived_view(',
        'def cmd_oracle_event_checkpoint(',
        'def cmd_oracle_horizon_view(',
        'def cmd_oracle_horizon_checkpoint(',
        'def cmd_verify_oracle_event_checkpoint(',
    ]:
        assert symbol in content
