from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_operator_runtime_commands_module_owns_split_cluster() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_operator_runtime_commands.py').read_text(encoding='utf-8')
    assert 'def register_oracle_operator_runtime_commands(' in helper
    assert 'oracle-operator-queue-query' in helper
    assert 'oracle-operator-control-plane-bundle' in helper
    assert 'oracle-operator-pack-query' in helper
    assert 'oracle-operator-pack-terminal-record-publish' in helper
    assert 'oracle-operator-pack-timeline' in helper


def test_rollout_ops_registers_operator_runtime_helper_module() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_operator_runtime_commands import register_oracle_operator_runtime_commands' in rollout_ops
    assert 'register_oracle_operator_runtime_commands(sub)' in rollout_ops
    assert 'register_oracle_queue_commands(sub, runners=' not in rollout_ops
    assert 'register_oracle_pack_commands(sub, runners=' not in rollout_ops
