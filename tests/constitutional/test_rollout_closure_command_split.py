from pathlib import Path


PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_closure_commands_module_owns_split_cluster() -> None:
    helper = (PKG_ROOT / 'cli' / 'rollout_closure_commands.py').read_text(encoding='utf-8')
    assert 'def register_rollout_closure_commands(' in helper
    assert 'def cmd_fingerprint(' in helper
    assert 'def cmd_bundle(' in helper
    assert 'def cmd_checklist(' in helper
    assert 'def cmd_review(' in helper
    assert 'def cmd_snapshot_keypair(' in helper
    assert 'def cmd_closure_snapshot(' in helper
    assert 'def cmd_governed_exception(' in helper
    assert 'def cmd_closure_attestation(' in helper
