from pathlib import Path


def test_rollout_ops_registers_briefing_replay_helper() -> None:
    text = Path("strategy_validator/cli/rollout_ops.py").read_text(encoding="utf-8")
    assert "from strategy_validator.cli.oracle_briefing_replay_commands import register_oracle_briefing_replay_commands" in text
    assert "register_oracle_briefing_replay_commands(" in text
    assert 'obp = sub.add_parser("oracle-briefing-pack"' not in text
    assert 'ora = sub.add_parser("oracle-replay-audit"' not in text
    assert 'ocsi = sub.add_parser(' not in text
    assert 'ocsr = sub.add_parser(' not in text
    assert 'ot = sub.add_parser("oracle-transition"' not in text


def test_briefing_replay_helper_owns_command_cluster() -> None:
    text = Path("strategy_validator/cli/oracle_briefing_replay_commands.py").read_text(encoding="utf-8")
    for marker in [
        'oracle-compacted-state-inspect',
        'oracle-compacted-state-rebuild',
        'oracle-briefing-pack',
        'oracle-replay-audit',
        'oracle-transition',
    ]:
        assert marker in text
    assert 'set_defaults(_run=runners["oracle-briefing-pack"])' in text
    assert 'set_defaults(_run=runners["oracle-replay-audit"])' in text
