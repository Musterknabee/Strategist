from pathlib import Path


def test_oracle_pack_commands_imports_runner_cluster() -> None:
    text = Path('strategy_validator/cli/oracle_pack_commands.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_pack_runners import (' in text
    assert 'cmd_oracle_operator_pack_query,' in text
    assert 'cmd_oracle_operator_pack_terminal_record_publish,' in text


def test_oracle_pack_commands_no_longer_defines_runner_wall_inline() -> None:
    text = Path('strategy_validator/cli/oracle_pack_commands.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_pack_query(' not in text
    assert 'def cmd_oracle_operator_pack_terminal_record_publish(' not in text


def test_oracle_pack_runners_is_compatibility_surface() -> None:
    text = Path('strategy_validator/cli/oracle_pack_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_pack_index_runners import *' in text
    assert 'from strategy_validator.cli.oracle_pack_lifecycle_runners import *' in text
    assert 'def cmd_oracle_operator_pack_query(' not in text
    assert 'def cmd_oracle_operator_pack_terminal_record_publish(' not in text
