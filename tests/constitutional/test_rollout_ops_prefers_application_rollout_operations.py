from pathlib import Path


PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_ops_prefers_application_rollout_operations() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.rollout_closure_commands import register_rollout_closure_commands' in rollout_ops
    assert 'register_rollout_closure_commands(' in rollout_ops
    assert 'from strategy_validator.validator.rollout_ops import (' not in rollout_ops
    assert 'def cmd_fingerprint' not in rollout_ops
    assert 'def cmd_bundle' not in rollout_ops
    assert 'def cmd_checklist' not in rollout_ops
    assert 'def cmd_review' not in rollout_ops
    assert 'def cmd_snapshot_keypair' not in rollout_ops
    assert 'def cmd_closure_snapshot' not in rollout_ops
