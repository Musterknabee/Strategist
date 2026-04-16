from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_chronic_queue_runners_module_is_compatibility_surface() -> None:
    chronic = (PKG_ROOT / 'cli' / 'oracle_queue_chronic_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_queue_monitoring_runners import *' in chronic
    assert 'from strategy_validator.cli.oracle_queue_recurrence_runners import *' in chronic
    assert 'def cmd_oracle_operator_chronic_exit_return_bridge(' not in chronic
    assert 'def cmd_oracle_operator_reopen_lineage(' not in chronic


def test_queue_monitoring_runners_module_owns_monitoring_cluster() -> None:
    monitoring = (PKG_ROOT / 'cli' / 'oracle_queue_monitoring_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_chronic_exit_return_bridge(' in monitoring
    assert 'def cmd_oracle_operator_return_monitoring(' in monitoring
    assert 'def cmd_oracle_operator_provenance_aware_drift_policy(' in monitoring
    assert 'def cmd_oracle_operator_reopen_lineage(' not in monitoring


def test_queue_recurrence_runners_module_owns_recurrence_cluster() -> None:
    recurrence = (PKG_ROOT / 'cli' / 'oracle_queue_recurrence_runners.py').read_text(encoding='utf-8')
    assert 'def cmd_oracle_operator_reopen_lineage(' in recurrence
    assert 'def cmd_oracle_operator_freeze_release_attestation(' in recurrence
    assert 'def cmd_oracle_operator_chronic_exit_certification(' in recurrence
    assert 'def cmd_oracle_operator_chronic_exit_return_bridge(' not in recurrence
