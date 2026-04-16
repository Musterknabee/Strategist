from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_oracle_queue_runners_module_is_compatibility_surface() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_queue_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_queue_primary_runners import *' in helper
    assert 'from strategy_validator.cli.oracle_queue_chronic_runners import *' in helper
    assert 'def cmd_oracle_operator_queue_query(' not in helper
    assert 'def cmd_oracle_operator_chronic_exit_certification(' not in helper


def test_oracle_queue_commands_imports_split_runners() -> None:
    queue_commands = (PKG_ROOT / 'cli' / 'oracle_queue_commands.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_queue_runners import (' in queue_commands
    assert 'cmd_oracle_operator_queue_query,' in queue_commands
    assert 'cmd_oracle_operator_escalation_packet,' in queue_commands
    assert 'cmd_oracle_operator_reentry_assignment,' in queue_commands
    assert 'cmd_oracle_operator_return_monitoring,' in queue_commands
    assert 'cmd_oracle_operator_control_plane_bundle,' in queue_commands
    assert 'cmd_oracle_operator_chronic_exit_certification,' in queue_commands
    assert 'def cmd_oracle_operator_queue_query(' not in queue_commands
    assert 'def cmd_oracle_operator_escalation_packet(' not in queue_commands
    assert 'def cmd_oracle_operator_reentry_assignment(' not in queue_commands
    assert 'def cmd_oracle_operator_return_monitoring(' not in queue_commands
    assert 'def cmd_oracle_operator_control_plane_bundle(' not in queue_commands
    assert 'def cmd_oracle_operator_chronic_exit_certification(' not in queue_commands
