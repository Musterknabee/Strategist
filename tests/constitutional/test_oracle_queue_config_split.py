from pathlib import Path


def test_oracle_queue_commands_imports_config_cluster() -> None:
    text = Path('strategy_validator/cli/oracle_queue_commands.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_queue_command_configs import (' in text
    assert '_configure_oracle_operator_queue_query,' in text
    assert '_configure_oracle_operator_chronic_exit_certification,' in text


def test_oracle_queue_commands_no_longer_defines_config_wall_inline() -> None:
    text = Path('strategy_validator/cli/oracle_queue_commands.py').read_text(encoding='utf-8')
    assert 'def _configure_oracle_operator_queue_query(' not in text
    assert 'def _configure_oracle_operator_chronic_exit_certification(' not in text


def test_oracle_queue_command_configs_owns_moved_config_cluster() -> None:
    text = Path('strategy_validator/cli/oracle_queue_command_configs.py').read_text(encoding='utf-8')
    assert 'def _configure_oracle_operator_queue_query(' in text
    assert 'def _configure_oracle_operator_chronic_exit_certification(' in text
