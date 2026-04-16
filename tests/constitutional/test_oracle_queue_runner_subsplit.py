from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_primary_queue_runners_module_owns_front_half() -> None:
    primary = (PKG_ROOT / 'cli' / 'oracle_queue_primary_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_queue_query(' in primary
    assert 'def cmd_oracle_operator_escalation_packet(' in primary
    assert 'def cmd_oracle_operator_reentry_completion(' in primary
    assert 'def cmd_oracle_operator_chronic_exit_return_bridge(' not in primary


def test_chronic_queue_runners_module_stays_out_of_primary_surface() -> None:
    chronic = (PKG_ROOT / 'cli' / 'oracle_queue_chronic_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_queue_query(' not in chronic
    assert 'from strategy_validator.cli.oracle_queue_monitoring_runners import *' in chronic
    assert 'from strategy_validator.cli.oracle_queue_recurrence_runners import *' in chronic


def test_queue_runner_common_module_owns_shared_helpers() -> None:
    common = (PKG_ROOT / 'cli' / 'oracle_queue_runner_common.py').read_text(encoding='utf-8')
    assert 'def _build_queue_state(' in common
    assert 'def _emit_payload(' in common
    assert 'def _parse_prior_reopen_counts(' in common
    assert 'def _build_queue_kwargs(' in common
