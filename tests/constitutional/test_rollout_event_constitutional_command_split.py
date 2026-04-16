from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_event_constitutional_commands_module_owns_split_cluster() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_event_constitutional_commands.py').read_text(encoding='utf-8')
    assert 'def register_oracle_event_constitutional_commands(' in helper
    assert 'oracle-transition-evidence' in helper
    assert 'oracle-memory-review' in helper
    assert 'oracle-weekly-digest' in helper
    assert 'oracle-constitutional-gate' in helper
    assert 'oracle-status-pack' in helper
    assert 'oracle-constitutional-gate' in helper
    assert 'oracle-status-pack' in helper
    assert 'oracle-incident-pack' in helper


def test_rollout_ops_registers_event_constitutional_helper_module() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_constitutional_commands import register_oracle_event_constitutional_commands' in rollout_ops
    assert 'register_oracle_event_constitutional_commands(' in rollout_ops
    assert 'ote = sub.add_parser("oracle-transition-evidence"' not in rollout_ops
    assert 'omr = sub.add_parser("oracle-memory-review"' not in rollout_ops
    assert 'owd = sub.add_parser("oracle-weekly-digest"' not in rollout_ops
    assert 'ocg = sub.add_parser("oracle-constitutional-gate"' not in rollout_ops
    assert 'osp = sub.add_parser("oracle-status-pack"' not in rollout_ops
