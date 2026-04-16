from pathlib import Path

PKG_ROOT = Path(__file__).resolve().parents[2] / 'strategy_validator'


def test_rollout_event_constitutional_runners_module_is_compatibility_surface() -> None:
    helper = (PKG_ROOT / 'cli' / 'oracle_event_constitutional_runners.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_review_runners import *' in helper
    assert 'from strategy_validator.cli.oracle_event_diagnostic_runners import *' in helper


def test_rollout_ops_imports_event_constitutional_runners() -> None:
    rollout_ops = (PKG_ROOT / 'cli' / 'rollout_ops.py').read_text(encoding='utf-8')
    assert 'from strategy_validator.cli.oracle_event_constitutional_runners import (' in rollout_ops
    for symbol in [
        'cmd_oracle_transition,',
        'cmd_oracle_memory_review,',
        'cmd_oracle_weekly_digest,',
        'cmd_oracle_constitutional_digest,',
        'cmd_oracle_explain,',
        'cmd_oracle_diagnose,',
        'cmd_oracle_status_pack,',
        'cmd_oracle_briefing_pack,',
        'cmd_oracle_replay_audit,',
    ]:
        assert symbol in rollout_ops
    for symbol in [
        'def cmd_oracle_transition(',
        'def cmd_oracle_memory_review(',
        'def cmd_oracle_weekly_digest(',
        'def cmd_oracle_constitutional_digest(',
        'def cmd_oracle_explain(',
        'def cmd_oracle_diagnose(',
        'def cmd_oracle_status_pack(',
        'def cmd_oracle_briefing_pack(',
        'def cmd_oracle_replay_audit(',
    ]:
        assert symbol not in rollout_ops
